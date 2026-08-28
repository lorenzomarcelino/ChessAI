from pathlib import Path

import torch
from torch import nn

from engine.encode import INPUT_PLANES, POLICY_SIZE

DEFAULT_CHANNELS = 64
DEFAULT_BLOCKS = 6
MODELS_DIR = Path(__file__).resolve().parents[1] / 'models'


class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x
        x = torch.relu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        return torch.relu(x + residual)


class CompactNet(nn.Module):
    """MLP barata para eval nas folhas (destilação Stockfish). Policy só na raiz."""

    ARCH = 'compact'

    def __init__(self, hidden=256, mid=32, in_features=None):
        super().__init__()
        self.hidden = hidden
        self.mid = mid
        in_features = in_features or (INPUT_PLANES * 64)
        self.fc1 = nn.Linear(in_features, hidden)
        self.fc2 = nn.Linear(hidden, mid)
        self.value_head = nn.Linear(mid, 1)
        self.policy_head = nn.Linear(hidden, POLICY_SIZE)

    def _hidden(self, x):
        if x.dim() == 4:
            x = x.flatten(1)
        return torch.relu(self.fc1(x))

    def forward_value(self, x):
        h = self._hidden(x)
        return torch.tanh(self.value_head(torch.relu(self.fc2(h)))).squeeze(-1)

    def forward(self, x):
        h = self._hidden(x)
        value = torch.tanh(self.value_head(torch.relu(self.fc2(h)))).squeeze(-1)
        policy = self.policy_head(h)
        return policy, value


class ValuePolicyNet(nn.Module):
    def __init__(self, in_planes=INPUT_PLANES, channels=DEFAULT_CHANNELS, blocks=DEFAULT_BLOCKS):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(in_planes, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
        )
        self.blocks = nn.Sequential(*[ResidualBlock(channels) for _ in range(blocks)])
        self.value_head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(channels, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, 1),
            nn.Tanh(),
        )
        # (N, 64, 8, 8) = origem × destino, sem camada linear enorme
        self.policy_conv = nn.Conv2d(channels, 64, 1)

    def forward(self, x):
        x = self.blocks(self.stem(x))
        value = self.value_head(x).squeeze(-1)
        policy = self.policy_conv(x).reshape(x.size(0), POLICY_SIZE)
        return policy, value


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def save_checkpoint(model, path, extra=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'state_dict': model.state_dict(),
        'params': count_parameters(model),
    }
    if isinstance(model, CompactNet):
        payload.update({
            'arch': CompactNet.ARCH,
            'hidden': model.hidden,
            'mid': model.mid,
        })
    else:
        payload.update({
            'arch': 'cnn',
            'in_planes': INPUT_PLANES,
            'channels': DEFAULT_CHANNELS,
            'blocks': DEFAULT_BLOCKS,
        })
    if extra:
        payload.update(extra)
    torch.save(payload, path)


def load_net(path, device=None):
    device = device or torch.device('cpu')
    payload = torch.load(path, map_location=device, weights_only=False)
    if payload.get('arch') == CompactNet.ARCH:
        model = CompactNet(
            hidden=payload.get('hidden', 256),
            mid=payload.get('mid', 32),
        )
    else:
        model = ValuePolicyNet(
            in_planes=payload.get('in_planes', INPUT_PLANES),
            channels=payload.get('channels', DEFAULT_CHANNELS),
            blocks=payload.get('blocks', DEFAULT_BLOCKS),
        )
    model.load_state_dict(payload['state_dict'])
    model.to(device)
    model.eval()
    return model, payload


def export_untrained(path=None):
    path = Path(path) if path else MODELS_DIR / 'untrained.pt'
    model = ValuePolicyNet()
    save_checkpoint(model, path, extra={'trained': False})
    return path, count_parameters(model)


if __name__ == '__main__':
    dest, n = export_untrained()
    print(f'{dest} ({n} parâmetros)')
