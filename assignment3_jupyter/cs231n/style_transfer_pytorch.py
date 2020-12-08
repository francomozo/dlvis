import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as T
import PIL

import numpy as np

from .image_utils import SQUEEZENET_MEAN, SQUEEZENET_STD

#dtype = torch.FloatTensor
# Uncomment out the following line if you're on a machine with a GPU set up for PyTorch!
dtype = torch.cuda.FloatTensor
def content_loss(content_weight, content_current, content_original):
    """
    Compute the content loss for style transfer.

    Inputs:
    - content_weight: Scalar giving the weighting for the content loss.
    - content_current: features of the current image; this is a PyTorch Tensor of shape
      (1, C_l, H_l, W_l).
    - content_target: features of the content image, Tensor with shape (1, C_l, H_l, W_l).

    Returns:
    - scalar content loss
    """
    # *****START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****

    _, C_l, H_l, W_l = content_current.size()

    content_current = torch.reshape(content_current, (1, C_l, H_l * W_l))
    content_original = torch.reshape(content_original, (1, C_l, H_l * W_l))

    return content_weight * torch.sum((content_current - content_original) ** 2)


    # *****END OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****

def gram_matrix(features, normalize=True):
    """
    Compute the Gram matrix from features.

    Inputs:
    - features: PyTorch Tensor of shape (N, C, H, W) giving features for
      a batch of N images.
    - normalize: optional, whether to normalize the Gram matrix
        If True, divide the Gram matrix by the number of neurons (H * W * C)

    Returns:
    - gram: PyTorch Tensor of shape (N, C, C) giving the
      (optionally normalized) Gram matrices for the N input images.
    """
    # *****START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****

    N, C, H, W = features.size()

    features = features.view(N, C, H * W)

    # no encontre una mejor forma que con 2 loops
    #for i in range(C):
    #    for j in range(C):
    #        gram[:, i, j] = torch.sum(
    #            features[:, i, :] * features[:, i, :], dim=1
    #        )

    # haciendo transpuesta es simplemente una multipl de matrices
    #for i in range(N):
    #    gram[i, :] = torch.mm(features[i, :], features[i, :].t() )

    # hay una funcion de pytorch que me soluciona sobre un batch
    gram = torch.bmm(features, torch.transpose(features, 1, 2))

    if normalize:
        gram = gram / ( H * W * C )

    return gram

    # *****END OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****

# Now put it together in the style_loss function...
def style_loss(feats, style_layers, style_targets, style_weights):
    """
    Computes the style loss at a set of layers.

    Inputs:
    - feats: list of the features at every layer of the current image, as produced by
      the extract_features function.
    - style_layers: List of layer indices into feats giving the layers to include in the
      style loss.
    - style_targets: List of the same length as style_layers, where style_targets[i] is
      a PyTorch Tensor giving the Gram matrix of the source style image computed at
      layer style_layers[i].
    - style_weights: List of the same length as style_layers, where style_weights[i]
      is a scalar giving the weight for the style loss at layer style_layers[i].

    Returns:
    - style_loss: A PyTorch Tensor holding a scalar giving the style loss.
    """
    # Hint: you can do this with one for loop over the style layers, and should
    # not be very much code (~5 lines). You will need to use your gram_matrix function.
    # *****START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****

    style_loss = 0

    for i in range(len(style_layers)):
        layer_idx = style_layers[i]

        style_loss += style_weights[i] * torch.sum(
            (gram_matrix(feats[layer_idx]) - style_targets[i]) ** 2
            )

    return style_loss

    # *****END OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****

def tv_loss(img, tv_weight):
    """
    Compute total variation loss.

    Inputs:
    - img: PyTorch Variable of shape (1, 3, H, W) holding an input image.
    - tv_weight: Scalar giving the weight w_t to use for the TV loss.

    Returns:
    - loss: PyTorch Variable holding a scalar giving the total variation loss
      for img weighted by tv_weight.
    """
    # Your implementation should be vectorized and not require any loops!
    # *****START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****

    # creo matrices auxiliares operando sobre img para no usar loops
    #img_i = img[:, :, :-1, :]
    #img_iplus1 = img[:, :, 1:, :]

    # contiene la matriz diferencia con las filas x_{i+1} - x_i
    #img_diff = img_iplus1 - img_i

    # ahora preciso elevar al cuadrado termino a termino y sumar sobre todos los canales
    #tv_loss_term1 = torch.sum(img_diff ** 2)

    # haciendo transpuesta y mismo procedimiento obtengo el segundo termino
    #transposed_img = torch.transpose(img, 1, 2)

    #img_j = transposed_img[:, :, :-1, :]
    #img_jplus1 = transposed_img[:, :, 1:, :]

    #img_diffj = img_jplus1 - img_j
    #tv_loss_term2 = torch.sum(img_diffj ** 2)
    # algo me esta funcionando mal con la transpuesta (creo)
    # y se puede hacer bien indexando segun j

    tv_loss_term1 = torch.sum((img[:, :, 1:, :] - img[:, :, :-1, :]) **2)
    tv_loss_term2 = torch.sum((img[:, :, :, 1:] - img[:, :, :, :-1]) **2)

    return tv_weight * (tv_loss_term1 + tv_loss_term2)
    # *****END OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****


def preprocess(img, size=512):
    """ Preprocesses a PIL JPG Image object to become a Pytorch tensor
        that is ready to be used as an input into the CNN model.
        Preprocessing steps:
            1) Resize the image (preserving aspect ratio) until the shortest side is of length `size`.
            2) Convert the PIL Image to a Pytorch Tensor.
            3) Normalize the mean of the image pixel values to be SqueezeNet's expected mean, and
                 the standard deviation to be SqueezeNet's expected std dev.
            4) Add a batch dimension in the first position of the tensor: aka, a tensor of shape
                 (H, W, C) will become -> (1, H, W, C).
    """
    transform = T.Compose([
        T.Resize(size),
        T.ToTensor(),
        T.Normalize(mean=SQUEEZENET_MEAN.tolist(),
                    std=SQUEEZENET_STD.tolist()),
        T.Lambda(lambda x: x[None]),
    ])
    return transform(img)

def deprocess(img):
    """ De-processes a Pytorch tensor from the output of the CNN model to become
        a PIL JPG Image that we can display, save, etc.
        De-processing steps:
            1) Remove the batch dimension at the first position by accessing the slice at index 0.
                 A tensor of dims (1, H, W, C) will become -> (H, W, C).
            2) Normalize the standard deviation: multiply each channel of the output tensor by 1/s,
                 scaling the elements back to before scaling by SqueezeNet's standard devs.
                 No change to the mean.
            3) Normalize the mean: subtract the mean (hence the -m) from each channel of the output tensor,
                 centering the elements back to before centering on SqueezeNet's input mean.
                 No change to the std dev.
            4) Rescale all the values in the tensor so that they lie in the interval [0, 1] to prepare for
                 transforming it into image pixel values.
            5) Convert the Pytorch Tensor to a PIL Image.
    """
    transform = T.Compose([
        T.Lambda(lambda x: x[0]),
        T.Normalize(mean=[0, 0, 0], std=[1.0 / s for s in SQUEEZENET_STD.tolist()]),
        T.Normalize(mean=[-m for m in SQUEEZENET_MEAN.tolist()], std=[1, 1, 1]),
        T.Lambda(rescale),
        T.ToPILImage(),
    ])
    return transform(img)

def rescale(x):
    """ A function used internally inside `deprocess`.
        Rescale elements of x linearly to be in the interval [0, 1]
        with the minimum element(s) mapped to 0, and the maximum element(s)
        mapped to 1.
    """
    low, high = x.min(), x.max()
    x_rescaled = (x - low) / (high - low)
    return x_rescaled

def rel_error(x,y):
    return np.max(np.abs(x - y) / (np.maximum(1e-8, np.abs(x) + np.abs(y))))

# We provide this helper code which takes an image, a model (cnn), and returns a list of
# feature maps, one per layer.
def extract_features(x, cnn):
    """
    Use the CNN to extract features from the input image x.

    Inputs:
    - x: A PyTorch Tensor of shape (N, C, H, W) holding a minibatch of images that
      will be fed to the CNN.
    - cnn: A PyTorch model that we will use to extract features.

    Returns:
    - features: A list of feature for the input images x extracted using the cnn model.
      features[i] is a PyTorch Tensor of shape (N, C_i, H_i, W_i); recall that features
      from different layers of the network may have different numbers of channels (C_i) and
      spatial dimensions (H_i, W_i).
    """
    features = []
    prev_feat = x
    for i, module in enumerate(cnn._modules.values()):
        next_feat = module(prev_feat)
        features.append(next_feat)
        prev_feat = next_feat
    return features

#please disregard warnings about initialization
def features_from_img(imgpath, imgsize, cnn):
    img = preprocess(PIL.Image.open(imgpath), size=imgsize)
    img_var = img.type(dtype)
    return extract_features(img_var, cnn), img_var




