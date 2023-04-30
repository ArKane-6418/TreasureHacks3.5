import torch.nn as nn
import torchvision
import torchvision.transforms as T
import torchvision.transforms.functional


# Reference:
#   https://github.com/richzhang/PerceptualSimilarity/blob/master/lpips/pretrained_networks.py#L96
class PretrainedVGG16(nn.Module):

    def __init__(self):
        super().__init__()

        vgg16 = torchvision.models.vgg16(weights=torchvision.models.VGG16_Weights.IMAGENET1K_FEATURES)
        vgg_pretrained_features = vgg16.features

        self.slice1 = nn.Sequential()
        self.slice2 = nn.Sequential()
        self.slice3 = nn.Sequential()
        self.slice4 = nn.Sequential()
        for x in range(4):
            self.slice1.add_module(str(x), vgg_pretrained_features[x])
        for x in range(4, 9):
            self.slice2.add_module(str(x), vgg_pretrained_features[x])
        for x in range(9, 16):
            self.slice3.add_module(str(x), vgg_pretrained_features[x])
        for x in range(16, 23):
            self.slice4.add_module(str(x), vgg_pretrained_features[x])

        self.requires_grad_(False)

    def forward(self, x):
        x = T.functional.normalize(x, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

        h = self.slice1(x)
        h_relu1_2 = h  # <- (AL) I've qualitatively found better samples by ignoring this
        h = self.slice2(h)
        h_relu2_2 = h
        h = self.slice3(h)
        h_relu3_3 = h
        h = self.slice4(h)
        h_relu4_3 = h

        return [h_relu2_2, h_relu3_3, h_relu4_3]
