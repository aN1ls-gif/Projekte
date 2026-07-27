# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 20:50:45 2026

@author: Nils
"""

# import torch
import torch
import torch.nn as nn
from torch.utils.data import Dataset
import pytorch_lightning as pl
from torch.optim.lr_scheduler import ReduceLROnPlateau


class Dataset_WordEmbedding(Dataset):
    """
    Dataset-class for the query and product strings that have been embedded into input_ids (and attention_masks) as well as the encoded esci-labels
    """
    def __init__(self, hp, input_ids, attention_masks, esci_labelencoded):
        self.hp = hp
        
        self.product_input_ids = input_ids.iloc[:, :(self.hp.tensor_size+1)*5+1]
        self.query_input_ids = input_ids.iloc[:, (self.hp.tensor_size+1)*5+1:]
        
        self.product_attention_masks = attention_masks.iloc[:, :(self.hp.tensor_size+1)*5+1]
        self.query_attention_masks = attention_masks.iloc[: ,(self.hp.tensor_size+1)*5+1:]
    
        self.esci_labelencoded = esci_labelencoded

    def __len__(self):
        return len(self.esci_labelencoded)

    def __getitem__(self, idx):
        pii = torch.tensor(self.product_input_ids.iloc[idx, :].to_numpy(), dtype = torch.int32)
        qii = torch.tensor(self.query_input_ids.iloc[idx, :].to_numpy(), dtype = torch.int32)
        
        pam = torch.tensor(self.product_attention_masks.iloc[idx, :].to_numpy(), dtype = torch.float32)
        qam = torch.tensor(self.query_attention_masks.iloc[idx, :].to_numpy(), dtype = torch.float32)
        
        true_label = torch.tensor(self.esci_labelencoded.iloc[idx], dtype = torch.int32)

        return pii, qii, pam, qam, true_label
    

class SimpleBERTModel(nn.Module):
    """
    A basic simple transformer encoder.
    Goal: Create an embedding for the query and the product and compute their cosine similarity.
    """
    def __init__(self, in_features, nhead):
        super().__init__()
        self.encoder_layer = nn.TransformerEncoderLayer(
            d_model = in_features,
            nhead = nhead,
            dim_feedforward=1024,
            dropout = 0.1,
            activation = "relu"
            )
        ## initialize the weights of the individual layers after initializing them. If not, they are all identical.
        self.transformer_encoder = nn.TransformerEncoder(
            self.encoder_layer,
            num_layers = 4
            )
        
    def forward(self, input_ids, attention_masks):
        output = self.transformer_encoder(src = input_ids, src_key_padding_mask = attention_masks)
        return output
        
        ### isolate the CLS token and so I can use it to compare query and product overall sentence information
        
    
class Similarity_to_class(nn.Module):
    """
    Intakes the similarity of the product and query tower and outputs the Esci label class.
    """
    def __init__(self, in_nodes, num_classes):
        super().__init__()

        self.fc1 = nn.Linear(in_nodes, in_nodes//4)
        self.fc2 = nn.Linear(in_nodes//4, in_nodes//16)
        self.out = nn.Linear(in_nodes//16, num_classes)
        
        self.fcbn1 = nn.BatchNorm1d(in_nodes//4)
        self.fcbn2 = nn.BatchNorm1d(in_nodes//16)
        
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)



    def forward(self, x):
        x = self.dropout(self.relu(self.fcbn1(self.fc1(x))))
        x = self.dropout(self.relu(self.fcbn2(self.fc2(x))))
        x = self.out(x)
        return x
        
    
class LearnedPositionEncoding(nn.Module): 
    """
    Simple Implementation of Positional Embedding for the Input_IDs given to the BERT.
    """
    def __init__(self, hp):
        super().__init__()
        self.position_embeddings = nn.Embedding(num_embeddings = hp.bert_vocab_size, embedding_dim = hp.bert_embedding_size)
 
    def forward(self, x):
        seq_len = x.size(0)
        position_ids = torch.arange(seq_len, dtype=torch.long, device=x.device).unsqueeze(1)
        position_embeds = self.position_embeddings(position_ids)
        x = x + position_embeds
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
    def __init__(self, hp, class_weights, num_classes, device):
        super().__init__()
        self.hp = hp
        self.num_classes = num_classes
        self.weights = class_weights # E S C I
        # self.adjusted_cossim_strength = torch.tensor([1]).to(device)
        # self.mean_for_C_shift = torch.tensor([-0.3]).to(device)
        # self.mean_for_S_shift = torch.tensor([0.3]).to(device)
        # self.std_for_norm_dist = torch.tensor([0.399]).to(device) # this makes it so that the y for the mean of the distribution is roughly 1
        
        self.query_input_embedding = nn.Embedding(num_embeddings = self.hp.bert_vocab_size, embedding_dim = self.hp.bert_embedding_size)
        self.query_positional_embedding = LearnedPositionEncoding(hp = self.hp)
        
        self.product_input_embedding = nn.Embedding(num_embeddings = self.hp.bert_vocab_size, embedding_dim = self.hp.bert_embedding_size)
        self.product_positional_embedding = LearnedPositionEncoding(hp = self.hp)

        self.query_tower = SimpleBERTModel(in_features = self.hp.bert_embedding_size, nhead = self.hp.bert_nheads)
        self.product_tower = SimpleBERTModel(in_features = self.hp.bert_embedding_size, nhead = self.hp.bert_nheads)
        self.sim_to_class = Similarity_to_class(in_nodes = self.hp.bert_embedding_size, num_classes = num_classes)


        # nn.BCEWithLogitsLoss
        self.ce_loss_fn_weighted = nn.CrossEntropyLoss(reduction = "mean", weight = self.weights)
        self.ce_loss_fn_unweighted = nn.CrossEntropyLoss(reduction = "mean")
        # self.cos_loss = nn.CosineSimilarity(dim = 1)
        # self.onehot = lambda x: nn.functional.one_hot(x, num_classes = num_classes).to(device)

        self.cos_loss_limit = torch.tensor([2]).to(device)
        self.similarity_eps = torch.tensor([self.hp.similarity_eps]).to(device)

    # def Shifted_Normal_Dist(self, x, Mean):
    #     """
    #     Incentivising the model for E and I is easy. E-sim == 1 is good. I-sim gets inverted so -1 becomes 1 and 1 is good
    #     S and C are more difficult. As a solution, I create a normal distribution, where the y for the desired similarity value is roughly 1 and becomes lower for all other possible similarities
    #     """
    #     y = (self.std_for_norm_dist * (2*torch.pi)**0.5)**-1
    #     y = y * torch.exp( -1 * (torch.square(x - Mean)/torch.square(2*self.std_for_norm_dist) ))
    #     return y

    # def compute_adjusted_cossim(self, product, query, true_labels, weighted = True):
    #     CosSim = self.cos_loss(query, product) # -1 is worst, 1 is best.
    #     E_mask = true_labels == 0
    #     S_mask = true_labels == 1
    #     C_mask = true_labels == 2
    #     I_mask = true_labels == 3


    #     ####### Want to make mean of all values.

    #     ### All Similarities get pressed into a range from 0 to 1, with 1 representing the most desired cosine similarity
    #     CosSim[E_mask] = (CosSim[E_mask] + 1) / 2
    #     CosSim[I_mask] = (CosSim[I_mask] * -1 + 1) / 2
    #     CosSim[C_mask] = self.Shifted_Normal_Dist(x = CosSim[C_mask], Mean = self.mean_for_C_shift)
    #     CosSim[S_mask] = self.Shifted_Normal_Dist(x = CosSim[S_mask], Mean = self.mean_for_S_shift)


    #     if weighted:
    #         ### Similar to the CE Loss, I want the 
    #         weights_vector = true_labels.clone().type(torch.float32)
    #         weights_vector[E_mask] = self.weights[0]
    #         weights_vector[S_mask] = self.weights[1]
    #         weights_vector[C_mask] = self.weights[2]
    #         weights_vector[I_mask] = self.weights[3]
    #         weights_vector = weights_vector / torch.sum(weights_vector)
    #         CosSim = torch.sum(CosSim * weights_vector)
    #     else:
    #         CosSim = torch.mean(CosSim)

    #     # goal: decrease the value
    #     return  torch.abs(CosSim - 1)


    def partial_cosine_similarity(self, x1, x2):
        """
        This cosine similarity calculation skips the dimension reduction.
        The unreduced result will be used as input to calcualte the classes.
        """
        Zähler = x1*x2
        Nenner = torch.maximum(torch.linalg.norm(x1, dim = 1), self.similarity_eps)
        Nenner *= torch.maximum(torch.linalg.norm(x2, dim = 1), self.similarity_eps)
        Nenner = Nenner[:, None]
        return Zähler/Nenner


    def configure_optimizers(self):
        # "weigth decay" is L2 Regularizer
        optimizer = torch.optim.AdamW(self.parameters(), lr= self.hp.lr, weight_decay = self.hp.l2)
        scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=self.hp.lr_decay_gamma, patience=self.hp.lr_decay_stepsize, threshold = self.hp.lr_decay_threshold)
        return  {"optimizer": optimizer, "lr_scheduler": scheduler, "monitor": "train_loss"}


    def _foundation(self, batch, weighted = True):
        """
        The basic steps that will be needed for all operations of training, validation, testing and forward.
        """
        pii, qii, pam, qam, true_labels = batch
        
        pii = self.product_positional_embedding(self.product_input_embedding(pii)).permute(1, 0, 2)
        qii = self.query_positional_embedding(self.query_input_embedding(qii)).permute(1, 0, 2)
        
        product_cls = self.product_tower(pii, pam)[0, :, :].squeeze()
        query_cls = self.query_tower(qii, qam)[0, :, :].squeeze()
        
        # adjusted_cossim = self.compute_adjusted_cossim(product = product_cls, query = query_cls, true_labels = true_labels, weighted = weighted)
        

        # Cosine_Similarity goes from -1 (vectors completly opposite directions) to 1 (vectors are identical)
        # As I want to use the Similarity as a probability of how well the product matches the query, any similarity smaller than 0 is set to 0.
        Similarity = self.partial_cosine_similarity(product_cls, query_cls)

        Prediction = self.sim_to_class(Similarity)

        if weighted:
            loss_fn = self.ce_loss_fn_weighted
        else:
            loss_fn = self.ce_loss_fn_unweighted

        
        ce_loss = loss_fn(Prediction, true_labels.type(torch.long))
        
        acc = torch.mean((torch.argmax(Prediction.detach(), dim = 1) == true_labels).type(torch.float32))
     
        return ce_loss, acc # + self.adjusted_cossim_strength * adjusted_cossim

    def training_step(self, batch, batch_idx):
        loss, acc = self._foundation(batch, weighted = True)
        self.log("train_loss", loss)
        self.log("train_acc", acc)
        return loss

    def validation_step(self, batch, batch_idx):
        loss, acc = self._foundation(batch, weighted = False)
        # torch._dynamo.graph_break()
        self.log("val_loss", loss)
        self.log("val_acc", acc)

    def test_step(self, batch, batch_idx):
        loss, acc = self._foundation(batch, weighted = False)
        self.log("test_los", loss.detach())
        self.log("test_acc", acc)