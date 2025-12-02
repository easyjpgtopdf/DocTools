# ============================================
# U2Net Full Model Architecture
# Complete PyTorch Implementation
# Better Quality than U2NetP
# ============================================

import torch
import torch.nn as nn
import torch.nn.functional as F

class REBNCONV(nn.Module):
    def __init__(self, in_ch=3, out_ch=3, dirate=1):
        super(REBNCONV, self).__init__()
        self.conv_s1 = nn.Conv2d(in_ch, out_ch, 3, padding=1*dirate, dilation=1*dirate, bias=True)
        self.bn_s1 = nn.BatchNorm2d(out_ch)
        self.relu_s1 = nn.ReLU(inplace=True)

    def forward(self, x):
        hx = x
        xout = self.relu_s1(self.bn_s1(self.conv_s1(hx)))
        return xout

class RSU(nn.Module):
    def __init__(self, name, in_ch=3, mid_ch=12, out_ch=3):
        super(RSU, self).__init__()
        self.name = name
        self.rebnconvin = REBNCONV(in_ch, out_ch, dirate=1)
        self.rebnconv1 = REBNCONV(out_ch, mid_ch, dirate=1)
        self.pool1 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv2 = REBNCONV(mid_ch, mid_ch, dirate=1)
        self.pool2 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv3 = REBNCONV(mid_ch, mid_ch, dirate=1)
        self.pool3 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv4 = REBNCONV(mid_ch, mid_ch, dirate=1)
        self.pool4 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.rebnconv5 = REBNCONV(mid_ch, mid_ch, dirate=1)
        self.rebnconv6 = REBNCONV(mid_ch, mid_ch, dirate=2)
        self.rebnconv7 = REBNCONV(mid_ch*2, mid_ch, dirate=1)
        self.rebnconv8 = REBNCONV(mid_ch*2, mid_ch, dirate=1)
        self.rebnconv9 = REBNCONV(mid_ch*2, mid_ch, dirate=1)
        self.rebnconv10 = REBNCONV(mid_ch*2, out_ch, dirate=1)

    def forward(self, x):
        hx = x
        hxin = self.rebnconvin(hx)
        hx1 = self.rebnconv1(hxin)
        hx = self.pool1(hx1)
        hx2 = self.rebnconv2(hx)
        hx = self.pool2(hx2)
        hx3 = self.rebnconv3(hx)
        hx = self.pool3(hx3)
        hx4 = self.rebnconv4(hx)
        hx = self.pool4(hx4)
        hx5 = self.rebnconv5(hx)
        hx6 = self.rebnconv6(hx5)
        hx7 = self.rebnconv7(torch.cat((hx6, hx5), 1))
        hx6up = F.interpolate(hx7, size=hx4.shape[2:], mode='bilinear', align_corners=False)
        hx8 = self.rebnconv8(torch.cat((hx6up, hx4), 1))
        hx8up = F.interpolate(hx8, size=hx3.shape[2:], mode='bilinear', align_corners=False)
        hx9 = self.rebnconv9(torch.cat((hx8up, hx3), 1))
        hx9up = F.interpolate(hx9, size=hx2.shape[2:], mode='bilinear', align_corners=False)
        hx10 = self.rebnconv10(torch.cat((hx9up, hx2), 1))
        return hx10 + hxin

class U2NET(nn.Module):
    """U2Net Full Model - Better Quality than U2NetP"""
    def __init__(self, in_ch=3, out_ch=1):
        super(U2NET, self).__init__()
        self.stage1 = RSU("stage1", in_ch, 32, 64)
        self.pool12 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.stage2 = RSU("stage2", 64, 32, 128)
        self.pool23 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.stage3 = RSU("stage3", 128, 64, 256)
        self.pool34 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.stage4 = RSU("stage4", 256, 128, 512)
        self.pool45 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.stage5 = RSU("stage5", 512, 256, 512)
        self.pool56 = nn.MaxPool2d(2, stride=2, ceil_mode=True)
        self.stage6 = RSU("stage6", 512, 256, 512)
        self.stage6d = RSU("stage6d", 1024, 256, 512)
        self.stage5d = RSU("stage5d", 1024, 128, 256)
        self.stage4d = RSU("stage4d", 512, 64, 128)
        self.stage3d = RSU("stage3d", 256, 32, 64)
        self.stage2d = RSU("stage2d", 128, 16, 64)
        self.stage1d = RSU("stage1d", 128, 16, 64)
        self.side1 = nn.Conv2d(64, out_ch, 3, padding=1)
        self.side2 = nn.Conv2d(64, out_ch, 3, padding=1)
        self.side3 = nn.Conv2d(64, out_ch, 3, padding=1)
        self.side4 = nn.Conv2d(128, out_ch, 3, padding=1)
        self.side5 = nn.Conv2d(256, out_ch, 3, padding=1)
        self.side6 = nn.Conv2d(512, out_ch, 3, padding=1)
        self.outconv = nn.Conv2d(6, out_ch, 1)

    def forward(self, x):
        hx = x
        hx1 = self.stage1(hx)
        hx = self.pool12(hx1)
        hx2 = self.stage2(hx)
        hx = self.pool23(hx2)
        hx3 = self.stage3(hx)
        hx = self.pool34(hx3)
        hx4 = self.stage4(hx)
        hx = self.pool45(hx4)
        hx5 = self.stage5(hx)
        hx = self.pool56(hx5)
        hx6 = self.stage6(hx)
        hx6up = F.interpolate(hx6, size=hx5.shape[2:], mode='bilinear', align_corners=False)
        hx5d = self.stage6d(torch.cat((hx6up, hx5), 1))
        hx5dup = F.interpolate(hx5d, size=hx4.shape[2:], mode='bilinear', align_corners=False)
        hx4d = self.stage5d(torch.cat((hx5dup, hx4), 1))
        hx4dup = F.interpolate(hx4d, size=hx3.shape[2:], mode='bilinear', align_corners=False)
        hx3d = self.stage4d(torch.cat((hx4dup, hx3), 1))
        hx3dup = F.interpolate(hx3d, size=hx2.shape[2:], mode='bilinear', align_corners=False)
        hx2d = self.stage3d(torch.cat((hx3dup, hx2), 1))
        hx2dup = F.interpolate(hx2d, size=hx1.shape[2:], mode='bilinear', align_corners=False)
        hx1d = self.stage2d(torch.cat((hx2dup, hx1), 1))
        d1 = self.side1(hx1d)
        hx1dup = F.interpolate(hx1d, size=x.shape[2:], mode='bilinear', align_corners=False)
        hx0d = self.stage1d(torch.cat((hx1dup, x), 1))
        d0 = self.side2(hx0d)
        d2 = F.interpolate(self.side3(hx2d), size=x.shape[2:], mode='bilinear', align_corners=False)
        d3 = F.interpolate(self.side4(hx3d), size=x.shape[2:], mode='bilinear', align_corners=False)
        d4 = F.interpolate(self.side5(hx4d), size=x.shape[2:], mode='bilinear', align_corners=False)
        d5 = F.interpolate(self.side6(hx5d), size=x.shape[2:], mode='bilinear', align_corners=False)
        d6 = F.interpolate(self.side6(hx6), size=x.shape[2:], mode='bilinear', align_corners=False)
        d0 = self.outconv(torch.cat((d0, d1, d2, d3, d4, d5, d6), 1))
        return torch.sigmoid(d0)

