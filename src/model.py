import torch
import torch.nn as nn
from torchvision import models


class Encoder(nn.Module):
    def __init__ (self, hidden_size):
        super(Encoder, self).__init__()
        
        # Load pretrained resnet model
        resnet = models.resnet152(pretrained=True)
        
        # Remove the fully connected layers
        modules = list(resnet.children())[:-1]
        self.resnet = nn.Sequential(*modules)
        
        # Create our replacement layers
        # We reuse the in_feature size of the resnet fc layer for our first replacement layer = 2048 as of creation
        self.linear = nn.Linear(in_features = resnet.fc.in_features, out_features = hidden_size)
        self.bn = nn.BatchNorm1d(num_features = hidden_size, momentum = 0.01)

    def forward (self, images):
        # Get the expected output from the fully connected layers
        # Fn: AvgPool2d(kernel_size=7, stride=1, padding=0, ceil_mode=False, count_include_pad=True)
        # Output: torch.Size([batch_size, 2048, 1, 1])
        features = self.resnet(images)

        # Resize the features for our linear function
        features = features.view(features.size(0), -1)
        
        # Fn: Linear(in_features=2048, out_features=embed_size, bias=True)
        # Output: torch.Size([batch_size, embed_size])
        features = self.linear(features)
        
        # Fn: BatchNorm1d(embed_size, eps=1e-05, momentum=0.01, affine=True)
        # Output: torch.Size([batch_size, embed_size])
        features = self.bn(features)
        
        return features

class Classifier(nn.Module):
    def __init__ (self, hidden_size, num_classes=39):
        super(Classifier, self).__init__()

        self.model = torch.nn.Sequential(
            nn.Linear(in_features=hidden_size, out_features=512),
            nn.ReLU(),
            nn.Linear(in_features=512, out_features=512),
            nn.ReLU(),
            nn.Linear(in_features=512, out_features=512),
            nn.ReLU(),
            torch.nn.Softmax(dim=num_classes)
        )

    def forward (self, x):

        out = self.model(x)
        return out

class AdversarialHead(nn.Module):
    def __init__ (self, hidden_size):
        super(AdversarialHead, self).__init__()

        self.model = torch.nn.Sequential(
            nn.Linear(in_features=hidden_size, out_features=512),
            nn.ReLU(),
            nn.Linear(in_features=512, out_features=512),
            nn.ReLU(),
            nn.Linear(in_features=512, out_features=512),
            nn.ReLU(),
            torch.nn.Softmax(dim=1)
        )

    def forward (self, x):

        out = self.model(x)
        return out

class BaselineModel(nn.Module):
    def __init__ (self, hidden_size, num_classes=39):
        super(BaselineModel, self).__init__()

        self.encoder = Encoder(hidden_size)
        self.classifer = Classifier(hidden_size, num_classes)

    def forward (self, images):

        h = self.encoder(images)
        y = self.classifer(h)
        return y

class OurModel(nn.Module):
    def __init__ (self, hidden_size, num_classes=39):
        super(OurModel, self).__init__()

        self.encoder = Encoder(hidden_size)
        self.classifer = Classifier(hidden_size, num_classes)
        self.adv_head = AdversarialHead(hidden_size)

    def forward (self, images):

        h = self.encoder(images)
        y = self.classifer(h)
        a = self.adv_head(h)
        return y, a


