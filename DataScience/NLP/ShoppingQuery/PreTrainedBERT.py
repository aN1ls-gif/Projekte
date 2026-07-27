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

from transformers import BertModel
BERT = BertModel.from_pretrained("prajjwal1/bert-tiny")

# for name, layer in BERT.named_children():
#     print(name + ":", end = " ")
#     if name == "pooler":
#         print("Not Frozen")
#     else:
#         for param in layer.parameters():
#             param.requires_grad = False
#         print("Frozen")

# print(BERT.pooler)
latent_dim = BERT.pooler.dense.out_features

# for name, layer in BERT.encoder.layer.named_children():
#     print(f"encoder.layer.{name}:", end = " ")
#     if name == "11":
#         print("Not Frozen")
#     else:
#         for param in layer.parameters():
#             param.requires_grad = False
#         print("Frozen")
    


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
    def __init__(self):
        super().__init__()
        self.model = BERT
        
    def forward(self, input_ids, attention_masks):
        output = self.model(input_ids, attention_masks)
        return output.last_hidden_state
        
        ### isolate the CLS token and so I can use it to compare query and product overall sentence information
        
    
class Similarity_to_class(nn.Module):
    """
    Intakes the similarity of the product and query tower and outputs the Esci label class.
    """
    def __init__(self):
        super().__init__()

        in_nodes = latent_dim
        num_classes = 4
        self.fc1 = nn.Linear(in_nodes, in_nodes//4)
        self.fc2 = nn.Linear(in_nodes//4, in_nodes//16)
        self.out = nn.Linear(in_nodes//16, num_classes)
        
        self.fcbn1 = nn.BatchNorm1d(in_nodes//4)
        self.fcbn2 = nn.BatchNorm1d(in_nodes//16)

        # self.fc1 = nn.Linear(1, 50)
        # self.fc2 = nn.Linear(50, 20)
        # self.out = nn.Linear(20, 4)
        
        # self.fcbn1 = nn.BatchNorm1d(50)
        # self.fcbn2 = nn.BatchNorm1d(20)
        
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.1)



    def forward(self, x):
        x = self.dropout(self.relu(self.fcbn1(self.fc1(x))))
        x = self.dropout(self.relu(self.fcbn2(self.fc2(x))))
        x = self.out(x)
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
    def __init__(self, hp, class_weights, device):
        super().__init__()
        self.hp = hp
    
        self.query_tower = SimpleBERTModel()
        self.product_tower = SimpleBERTModel()
        self.sim_to_class = Similarity_to_class()


        # nn.BCEWithLogitsLoss
        self.ce_loss_fn_weighted = nn.CrossEntropyLoss(reduction = "mean", weight = class_weights)
        self.ce_loss_fn_unweighted = nn.CrossEntropyLoss(reduction = "mean")
        # self.cos_loss = nn.CosineSimilarity(dim = 1)
        self.similarity_eps = torch.tensor([1e-10]).to(device)


    def configure_optimizers(self):
        # "weigth decay" is L2 Regularizer
        optimizer = torch.optim.AdamW(self.parameters(), lr= self.hp.lr, weight_decay = self.hp.l2)
        scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=self.hp.lr_decay_gamma, patience=self.hp.lr_decay_stepsize, threshold = self.hp.lr_decay_threshold)
        return  {"optimizer": optimizer, "lr_scheduler": scheduler, "monitor": "train_loss"}

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


    def _foundation(self, batch, weighted = True):
        """
        The basic steps that will be needed for all operations of training, validation, testing and forward.
        """
        pii, qii, pam, qam, true_labels = batch
        
        ## isolating the cls token
        product_cls = self.product_tower(pii, pam)[:, 0, :].squeeze()
        query_cls = self.query_tower(qii, qam)[:, 0, :].squeeze()
        
        

        # Cosine_Similarity goes from -1 (vectors completly opposite directions) to 1 (vectors are identical)
        # As I want to use the Similarity as a probability of how well the product matches the query, any similarity smaller than 0 is set to 0.
        Similarity = self.partial_cosine_similarity(product_cls, query_cls)# [:, None]

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