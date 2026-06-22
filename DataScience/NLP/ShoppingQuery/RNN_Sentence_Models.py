import torch
import torch.nn as nn
import pytorch_lightning as pl
import numpy as np

from torch.utils.data import Dataset, DataLoader
Project_Name = "RNN_Sentences_CE"
tensor_size = 32

class Hyperparameters:
    ###### In Model
    lr = 1e-4
    l2 = 1e-5
    lr_decay_gamma = 0.1
    lr_decay_stepsize = 5
    lr_decay_threshold = 1e-3
    lr_decay_parameter = "train_loss"
    label_smoothing = 0.1
    similarity_eps = 1e-10

    ## Outside of model
    # gradient_accumulation_batches = 10
    gradient_clip_val = 1.0
    Epochs = 100
    earlyStopping_min_delta = 1e-8
    earlyStopping_patience = 25
    checkPoint_Path = f"Training_Progress/Checkpoints/{Project_Name}"
    checkPoint_FilenameBase = "TwoTowerRetrieval"




class Dataset_SentenceEmbedding(Dataset):
    """
    For Sentence Embedding.
    The different product_embedding are concatenated togehter into a single tensor.
    """
    def __init__(self, Dataset):
        self.product = Dataset.iloc[:, :tensor_size*6]

        self.query = Dataset.iloc[:, tensor_size*6:tensor_size*7]
        self.esci_labelencoded = Dataset.loc[:, ("esci_label_encoded", "")]

    def __len__(self):
        return len(self.query)


    def __getitem__(self, idx):
        product = torch.tensor(self.product.iloc[idx].to_numpy().astype(np.float32))# .type(torch.long)# .squeeze(0)
        query = torch.tensor(self.query.iloc[idx].to_numpy().astype(np.float32))# .type(torch.long).squeeze(0) # shape idx
        true_label = torch.tensor(self.esci_labelencoded.iloc[idx])

        return product, query, true_label

import torch.nn as nn
import pytorch_lightning as pl
from torch.optim.lr_scheduler import ReduceLROnPlateau

class Linear_Block(nn.Module):
    """
    Linear Layer building block containing a skip connection
    """
    def __init__(self, in_nodes, out_nodes, activ = "relu"):
        super().__init__()
        self.fc1 = nn.Linear(in_nodes, in_nodes)
        self.fc2 = nn.Linear(in_nodes, out_nodes)

        self.skip = nn.Identity() if in_nodes == out_nodes else nn.Linear(in_nodes, out_nodes)

        if activ == "relu":
            self.activ_f = nn.ReLU()
            for layer in [self.fc1, self.fc2, self.skip]:
                if isinstance(layer, nn.Linear):
                    nn.init.kaiming_uniform_(layer.weight, mode='fan_in', nonlinearity='relu')
        elif activ == "tanh":
            self.activ_f = nn.Tanh()
            for layer in [self.fc1, self.fc2, self.skip]:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight)
                    nn.init.zeros_(layer.bias)

        self.norm1 = nn.BatchNorm1d(in_nodes)
        self.norm2 = nn.BatchNorm1d(out_nodes)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        skip = self.skip(x)
        x = self.fc1(x)
        x = self.norm1(x)
        x = self.activ_f(x)
        x = self.dropout(x)

        x = self.fc2(x)
        x = self.norm2(x) + skip
        x = self.activ_f(x)
        x = self.dropout(x)
        return x



class Tower(nn.Module):
    """
    The basic tower for the query and prodcuts
    """
    def __init__(self, in_nodes, out_nodes, compressed_by = 2):
        super().__init__()

        # self.compression = nn.AvgPool1d(kernel_size = compressed_by, stride = compressed_by)

        self.skip = nn.Linear(1024, out_nodes)
        self.fc1 = Linear_Block(in_nodes, 1024)
        self.fc2 = Linear_Block(1024, 768)
        self.fc3 = Linear_Block(768, 512)
        self.fc4 = Linear_Block(512, 384)
        self.out = nn.Linear(384, out_nodes)

    def forward(self, x):
        # x = self.compression(x)
        x = self.fc1(x)
        skip = self.skip(x)
        x = self.fc2(x)
        x = self.fc3(x)
        x = self.fc4(x)
        x = self.out(x) + skip

        return x


class Similarity_to_class(nn.Module):
    """
    Intakes the similarity of the product and query tower and outputs the Esci label class.
    """
    def __init__(self, in_nodes, num_classes):
        super().__init__()

        self.fc1 =  Linear_Block(in_nodes, in_nodes//2)
        self.fc2 = Linear_Block(in_nodes//2, in_nodes//4)
        self.fc3 = Linear_Block(in_nodes//4, in_nodes//8)
        self.lstm = nn.LSTM(in_nodes//8, num_classes, num_layers=3, dropout=0.2)
        # self.out = nn.Linear(64, num_classes)
        self.skip = nn.Linear(in_nodes, num_classes)
       


    def forward(self, x):
        skip = self.skip(x)
        x = self.fc1(x)
        x = self.fc2(x)
        x = self.fc3(x)
        x, hidden = self.lstm(x)
        x = x + skip
        # x = self.out(x) + skip # logits
        return x


class Retrieval_Lightning(pl.LightningModule):
    """
    Creates two tower, one for handling the query embeddings and one for handling the product embeddings.
    Their similarity is computated using the cosine similarity. That similarity is then converted to the class-vector uitlizing LSTM.

    Parameters:
    ----------------
    out_nodes:
        Feature size of the tower-output. By default, the number of features is identitcal to the batch_size
    weights:
        Class weights for the training loss
    device:
        "cpu" or "gpu"/"cuda"
    num_classes:
        the number of features/classes in the final output
    hp:
        a class containing further hyperparameters
    """
    def __init__(self, out_nodes, weights, device, num_classes, hp):
        super().__init__()
        self.hp = hp
        self.num_classes = num_classes

        self.query_tower = Tower(in_nodes = tensor_size*1, out_nodes = out_nodes)
        self.product_tower = Tower(in_nodes = tensor_size*6, out_nodes = out_nodes)
        self.sim_to_class = Similarity_to_class(in_nodes = out_nodes, num_classes = num_classes)


        # nn.BCEWithLogitsLoss
        self.loss_fn_weighted = nn.CrossEntropyLoss(reduction = "mean", weight = weights, label_smoothing = hp.label_smoothing)# , label_smoothing = hp.label_smoothing)
        self.loss_fn_unweighted = nn.CrossEntropyLoss(reduction = "mean")
        # self.sim = nn.CosineSimilarity(dim = 1)
        # self.onehot = lambda x: nn.functional.one_hot(x, num_classes = num_classes).to(device)

        # These are for the custom logger callback
        self.training_step_outputs_loss = []
        self.validation_step_outputs_loss = []

        self.similarity_eps = torch.tensor([self.hp.similarity_eps]).to(device)

    def cosine_similarity(self, x1, x2):
        """
        This cosine similarity calculation skips the dimension reduction.
        The unreduced result will be used as input to calcualte the classes
        """
        Zähler = x1*x2
        Nenner = torch.maximum(torch.linalg.norm(x1, dim = 1), self.similarity_eps)
        Nenner *= torch.maximum(torch.linalg.norm(x2, dim = 1), self.similarity_eps)
        Nenner = Nenner[:, None]
        return Zähler/Nenner


    def configure_optimizers(self):
        # "weigth decay" is L2 Regularizer
        optimizer = torch.optim.AdamW(self.parameters(), lr= self.hp.lr, weight_decay = self.hp.l2)
        scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=hp.lr_decay_gamma, patience=hp.lr_decay_stepsize, threshold = hp.lr_decay_threshold)
        return  {"optimizer": optimizer, "lr_scheduler": scheduler, "monitor": "train_loss"}


    def _foundation(self, batch, weighted = True):
        """
        The basic steps that will be needed for all operations of training, validation, testing and forward.
        """
        # product and query are already sentece-embedded when provided by the DataLoader
        product, query, true_labels = batch

        query = self.query_tower(query)
        product = self.product_tower(product)
        # esci_onehot = self.onehot(esci_labels_encoded)

        # Cosine_Similarity goes from -1 (vectors completly opposite directions) to 1 (vectors are identical)
        # As I want to use the Similarity as a probability of how well the product matches the query, any similarity smaller than 0 is set to 0.
        Similarity = self.cosine_similarity(product, query)
        Prediction = self.sim_to_class(Similarity)

        if weighted:
            loss = self.loss_fn_weighted(Prediction, true_labels) # .transpose(0, 1).type(type(product))
        else:
            loss = self.loss_fn_unweighted(Prediction, true_labels) # .transpose(0, 1).type(type(product))
        return loss

    def training_step(self, batch, batch_idx):
        """
        Implement a single training period with loss function. Training loss is logged (by default to Tensorboard)
        """
        loss = self._foundation(batch, weighted = True)
        self.log("train_loss", loss)
        self.training_step_outputs_loss.append(loss.detach())
        return loss

    def validation_step(self, batch, batch_idx):
        """
        Implement a single training period with loss function. Training loss is logged (by default to Tensorboard)
        """
        loss = self._foundation(batch, weighted = False)
        # torch._dynamo.graph_break()
        self.log("val_loss", loss)
        self.validation_step_outputs_loss.append(loss.detach())
        return loss

    def test_step(self, batch, batch_idx):
        """
        Implement a single training period with loss function. Training loss is logged (by default to Tensorboard)
        """
        loss = self._foundation(batch, weighted = False)
        self.log("test_los", loss.detach())
        return loss
