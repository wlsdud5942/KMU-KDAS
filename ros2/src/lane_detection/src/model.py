import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from torchvision.models import VGG16_BN_Weights

class SCNN_LaneDetection(nn.Module):
    def __init__(self, input_size=(640, 480), ms_ks=9, pretrained=True):
        super(SCNN_LaneDetection, self).__init__()

        self.input_size = input_size
        self.pretrained = pretrained

        # VGG16 백본
        self.backbone = (
            models.vgg16_bn(weights=VGG16_BN_Weights.IMAGENET1K_V1).features
            if pretrained else models.vgg16_bn().features
        )

        self.net_init(input_size, ms_ks)
        if not pretrained:
            self.weight_init()

    def forward(self, img):
        x = self.backbone(img)
        x = self.layer1(x)
        x = self.message_passing_forward(x)
        x = self.layer2(x)

        # 2D 마스크 (logit)
        seg_pred = F.interpolate(x, size=(self.input_size[1], self.input_size[0]), mode='bilinear', align_corners=True)
        return seg_pred 

    def net_init(self, input_size, ms_ks):
        self.backbone = nn.Sequential(*list(self.backbone.children())[:-2])

        self.layer1 = nn.Sequential(
            nn.Conv2d(512, 1024, 3, padding=4, dilation=4, bias=False),
            nn.BatchNorm2d(1024),
            nn.ReLU(),
            nn.Conv2d(1024, 128, 1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU()
        )

        self.message_passing = nn.ModuleList([
            nn.Conv2d(128, 128, (1, ms_ks), padding=(0, ms_ks // 2), bias=False),
            nn.Conv2d(128, 128, (1, ms_ks), padding=(0, ms_ks // 2), bias=False),
            nn.Conv2d(128, 128, (ms_ks, 1), padding=(ms_ks // 2, 0), bias=False),
            nn.Conv2d(128, 128, (ms_ks, 1), padding=(ms_ks // 2, 0), bias=False)
        ])

        self.layer2 = nn.Sequential(
            nn.Dropout2d(0.1),
            nn.Conv2d(128, 1, 1)
        )

    def message_passing_forward(self, x):
        Vertical = [True, True, False, False]
        Reverse = [False, True, False, True]
        for conv, v, r in zip(self.message_passing, Vertical, Reverse):
            x = self.message_passing_once(x, conv, vertical=v, reverse=r)
        return x

    def message_passing_once(self, x, conv, vertical=True, reverse=False):
        nB, C, H, W = x.shape
        if vertical:
            slices = [x[:, :, i:(i+1), :] for i in range(H)]
            dim = 2
        else:
            slices = [x[:, :, :, i:(i+1)] for i in range(W)]
            dim = 3
        if reverse:
            slices = slices[::-1]

        out = [slices[0]]
        for i in range(1, len(slices)):
            out.append(slices[i] + F.relu(conv(out[i - 1])))
        if reverse:
            out = out[::-1]
        return torch.cat(out, dim=dim)

    def weight_init(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)


__all__ = ['SCNN_LaneDetection']