import math
import struct
import zlib
from pathlib import Path


WHITE = (255, 255, 255)
GRID = (225, 225, 225)
AXIS = (80, 80, 80)
BLUE = (31, 119, 180)
RED = (214, 39, 40)
GREEN = (44, 160, 44)
ORANGE = (255, 127, 14)


def write_line_chart(path, series, width=900, height=420):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image = _canvas(width, height)
    _draw_axes(image)

    colors = [BLUE, RED, GREEN, ORANGE]
    for index, values in enumerate(series):
        if values:
            _draw_series(image, values, colors[index % len(colors)])

    _write_png(path, image)


def write_bar_chart(path, values, width=900, height=420, color=BLUE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image = _canvas(width, height)
    _draw_axes(image)
    if values:
        _draw_bars(image, values, color)
    _write_png(path, image)


def write_histogram(path, values, bins=12, width=900, height=420):
    if not values:
        return write_bar_chart(path, [], width=width, height=height)

    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        buckets = [0] * bins
        buckets[bins // 2] = len(values)
        return write_bar_chart(path, buckets, width=width, height=height, color=GREEN)

    bucket_size = (maximum - minimum) / bins
    buckets = [0] * bins
    for value in values:
        index = min(bins - 1, int((value - minimum) / bucket_size))
        buckets[index] += 1
    return write_bar_chart(path, buckets, width=width, height=height, color=GREEN)


def _canvas(width, height):
    return [[WHITE for _ in range(width)] for _ in range(height)]


def _draw_axes(image):
    width = len(image[0])
    height = len(image)
    left = 56
    right = width - 24
    top = 24
    bottom = height - 48
    for x in range(left, right + 1):
        image[bottom][x] = AXIS
    for y in range(top, bottom + 1):
        image[y][left] = AXIS
    for step in range(1, 5):
        y = bottom - int((bottom - top) * step / 5)
        for x in range(left, right + 1):
            if x % 6 == 0:
                image[y][x] = GRID


def _draw_series(image, values, color):
    width = len(image[0])
    height = len(image)
    left = 56
    right = width - 24
    top = 24
    bottom = height - 48
    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        minimum -= 1
        maximum += 1

    points = []
    for index, value in enumerate(values):
        x = left + int((right - left) * index / max(1, len(values) - 1))
        y = bottom - int((bottom - top) * (value - minimum) / (maximum - minimum))
        points.append((x, y))

    for start, end in zip(points, points[1:]):
        _draw_line(image, start, end, color)


def _draw_bars(image, values, color):
    width = len(image[0])
    height = len(image)
    left = 56
    right = width - 24
    top = 24
    bottom = height - 48
    minimum = min(0, min(values))
    maximum = max(values)
    if minimum == maximum:
        maximum += 1

    bar_width = max(1, math.floor((right - left) / max(1, len(values))))
    zero_y = bottom - int((bottom - top) * (0 - minimum) / (maximum - minimum))
    for index, value in enumerate(values):
        x0 = left + index * bar_width
        x1 = min(right, x0 + max(1, bar_width - 2))
        y = bottom - int((bottom - top) * (value - minimum) / (maximum - minimum))
        y0, y1 = sorted((zero_y, y))
        _fill_rect(image, x0, y0, x1, y1, color)


def _draw_line(image, start, end, color):
    x0, y0 = start
    x1, y1 = end
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        _set_pixel(image, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        next_error = 2 * error
        if next_error >= dy:
            error += dy
            x0 += sx
        if next_error <= dx:
            error += dx
            y0 += sy


def _fill_rect(image, x0, y0, x1, y1, color):
    for y in range(max(0, y0), min(len(image), y1 + 1)):
        for x in range(max(0, x0), min(len(image[0]), x1 + 1)):
            image[y][x] = color


def _set_pixel(image, x, y, color):
    if 0 <= y < len(image) and 0 <= x < len(image[0]):
        image[y][x] = color


def _write_png(path, image):
    height = len(image)
    width = len(image[0])
    raw_rows = []
    for row in image:
        raw_rows.append(b"\x00" + b"".join(bytes(pixel) for pixel in row))
    raw = b"".join(raw_rows)
    with Path(path).open("wb") as file:
        file.write(b"\x89PNG\r\n\x1a\n")
        _write_chunk(file, b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        _write_chunk(file, b"IDAT", zlib.compress(raw))
        _write_chunk(file, b"IEND", b"")


def _write_chunk(file, chunk_type, data):
    file.write(struct.pack(">I", len(data)))
    file.write(chunk_type)
    file.write(data)
    checksum = zlib.crc32(chunk_type)
    checksum = zlib.crc32(data, checksum)
    file.write(struct.pack(">I", checksum & 0xFFFFFFFF))
