import pyasge


# handy component to check for intersections everywhere in the program
def floatIntersects(r1_x, r1_y, r1_width, r1_height, r2_x, r2_y, r2_width, r2_height):
    r1_x_max = max(r1_x, r1_x + r1_width)
    r1_x_min = min(r1_x, r1_x + r1_width)
    r1_y_max = max(r1_y, r1_y + r1_height)
    r1_y_min = min(r1_y, r1_y + r1_height)

    r2_x_max = max(r2_x, r2_x + r2_width)
    r2_x_min = min(r2_x, r2_x + r2_width)
    r2_y_max = max(r2_y, r2_y + r2_height)
    r2_y_min = min(r2_y, r2_y + r2_height)

    intersection_x_min = max(r1_x_min, r2_x_min)
    intersection_x_max = min(r1_x_max, r2_x_max)
    intersection_y_min = max(r1_y_min, r2_y_min)
    intersection_y_max = min(r1_y_max, r2_y_max)

    if intersection_x_min < intersection_x_max and intersection_y_min < intersection_y_max:
        return True

    return False


def spriteIntersects(r1: pyasge.Sprite, r2: pyasge.Sprite):
    r1 = r1.getWorldBounds()
    r2 = r2.getWorldBounds()

    r1_x_max = max(r1.v1.x, r1.v2.x)
    r1_x_min = min(r1.v1.x, r1.v2.x)
    r1_y_max = max(r1.v1.y, r1.v3.y)
    r1_y_min = min(r1.v1.y, r1.v3.y)

    r2_x_max = max(r2.v1.x, r2.v2.x)
    r2_x_min = min(r2.v1.x, r2.v2.x)
    r2_y_max = max(r2.v1.y, r2.v3.y)
    r2_y_min = min(r2.v1.y, r2.v3.y)

    intersection_x_min = max(r1_x_min, r2_x_min)
    intersection_x_max = min(r1_x_max, r2_x_max)
    intersection_y_min = max(r1_y_min, r2_y_min)
    intersection_y_max = min(r1_y_max, r2_y_max)

    if intersection_x_min < intersection_x_max and intersection_y_min < intersection_y_max:
        return True

    return False
