import keras.backend
import numpy


def anchor(base_size=16, ratios=None, scales=None):
    """
    Generates a regular grid of multi-aspect and multi-scale anchor boxes.
    """
    if ratios is None:
        ratios = keras.backend.variable(numpy.array([0.5, 1, 2]))

    if scales is None:
        scales = keras.backend.variable(numpy.array([8, 16, 32]))

    base_anchor = keras.backend.variable(numpy.array([1, 1, base_size, base_size]) - 1)

    ratio_anchors = _ratio_enum(base_anchor, ratios)

    anchors = keras.backend.concatenate([_scale_enum(ratio_anchors[i, :], scales) for i in range(ratio_anchors.shape[0])], axis = 0)

    return anchors


def bbox_transform(ex_rois, gt_rois):
    ex_widths = ex_rois[:, 2] - ex_rois[:, 0] + 1.0
    ex_heights = ex_rois[:, 3] - ex_rois[:, 1] + 1.0
    ex_ctr_x = ex_rois[:, 0] + 0.5 * ex_widths
    ex_ctr_y = ex_rois[:, 1] + 0.5 * ex_heights

    gt_widths = gt_rois[:, 2] - gt_rois[:, 0] + 1.0
    gt_heights = gt_rois[:, 3] - gt_rois[:, 1] + 1.0
    gt_ctr_x = gt_rois[:, 0] + 0.5 * gt_widths
    gt_ctr_y = gt_rois[:, 1] + 0.5 * gt_heights

    targets_dx = (gt_ctr_x - ex_ctr_x) / ex_widths
    targets_dy = (gt_ctr_y - ex_ctr_y) / ex_heights
    targets_dw = keras.backend.log(gt_widths / ex_widths)
    targets_dh = keras.backend.log(gt_heights / ex_heights)

    targets = keras.backend.stack((targets_dx, targets_dy, targets_dw, targets_dh))

    targets = keras.backend.transpose(targets)

    return targets


def clip(boxes, shape):
    proposals = [
        keras.backend.maximum(keras.backend.minimum(boxes[:, 0::4], shape[1] - 1), 0),
        keras.backend.maximum(keras.backend.minimum(boxes[:, 1::4], shape[1] - 1), 0),
        keras.backend.maximum(keras.backend.minimum(boxes[:, 2::4], shape[1] - 1), 0),
        keras.backend.maximum(keras.backend.minimum(boxes[:, 3::4], shape[0] - 1), 0)
    ]

    return keras.backend.concatenate(proposals)


def _mkanchors(ws, hs, x_ctr, y_ctr):
    """
    Given a vector of widths (ws) and heights (hs) around a center
    (x_ctr, y_ctr), output a set of anchors (windows).
    """

    ws = keras.backend.expand_dims(ws, axis=1)
    hs = keras.backend.expand_dims(hs, axis=1)

    anchors = keras.backend.concatenate((x_ctr - 0.5 * (ws - 1),
                                         y_ctr - 0.5 * (hs - 1),
                                         x_ctr + 0.5 * (ws - 1),
                                         y_ctr + 0.5 * (hs - 1)), axis=1)
    return anchors


def _ratio_enum(anchor, ratios):
    """
    Enumerate a set of anchors for each aspect ratio wrt an anchor.
    """

    w, h, x_ctr, y_ctr = _whctrs(anchor)
    size = w * h
    size_ratios = size / ratios
    ws = keras.backend.round(keras.backend.sqrt(size_ratios))
    hs = keras.backend.round(ws * ratios)
    anchors = _mkanchors(ws, hs, x_ctr, y_ctr)
    return anchors


def _scale_enum(anchor, scales):
    """
    Enumerate a set of anchors for each scale wrt an anchor.
    """

    w, h, x_ctr, y_ctr = _whctrs(anchor)
    ws = w * scales
    hs = h * scales
    anchors = _mkanchors(ws, hs, x_ctr, y_ctr)
    return anchors


def _whctrs(anchor):
    """
    Return width, height, x center, and y center for an anchor (window).
    """

    w = anchor[2] - anchor[0] + 1
    h = anchor[3] - anchor[1] + 1
    x_ctr = anchor[0] + 0.5 * (w - 1)
    y_ctr = anchor[1] + 0.5 * (h - 1)
    return w, h, x_ctr, y_ctr
