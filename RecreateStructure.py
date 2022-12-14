import numpy as np
from math import atan, pi
from BlurArray import blur

def recreateStructure(Xtilt_real, Ytilt_real, progress_callback):
    """
    This function uses the pitch (Xtilt_real) and roll (Ytilt_real) values for each square to recreate the relative
    heights of each post on the structure
    :param Xtilt_real: contains the pitch value of each square
    :param Ytilt_real: contains the roll value of each square
    :param progress_callback: returns the progress of the structure recreation process
    :return Zheight_recreated: returns the recreated structure values
    :return Zheight_lowpass: returns the "smoothed" structure values
    :return Zheight_delta: returns the difference between the recreated structure and the smoothed structure
    """

    size_x = len(Xtilt_real[0]) + 1
    size_y = len(Xtilt_real) + 1

    Zheight_recreated = np.zeros((size_y, size_x), float)

    last_progress = 0

    for i in range(1000):

        Xtilt_recreated = np.zeros((size_y - 1, size_x - 1), float)
        Xtilt_recreated[:] = np.NaN

        Ytilt_recreated = np.zeros((size_y - 1, size_x - 1), float)
        Ytilt_recreated[:] = np.NaN

        for y in range(size_y - 1):
            for x in range(size_x - 1):

                tempX = (Zheight_recreated[y, x + 1] + Zheight_recreated[y + 1, x + 1]) / 2 - (
                            Zheight_recreated[y, x] + Zheight_recreated[y + 1, x]) / 2
                tempX_rad = atan(tempX / 725)
                tempX_deg = atan(tempX_rad) * (180 / pi)

                Xtilt_recreated[y, x] = tempX_deg

                tempY = (Zheight_recreated[y + 1, x] + Zheight_recreated[y + 1, x + 1]) / 2 - (
                            Zheight_recreated[y, x] + Zheight_recreated[y, x + 1]) / 2
                tempY_rad = atan(tempY / 725)
                tempY_deg = atan(tempY_rad) * (180 / pi)

                Ytilt_recreated[y, x] = tempY_deg


        # calculate difference between real X-tilt values and recreated X-tilt values
        Xtilt_error = np.subtract(Xtilt_real, Xtilt_recreated)
        Ytilt_error = np.subtract(Ytilt_real, Ytilt_recreated)

        convergence = 0

        for x in range(size_x):
            for y in range(size_y):

                # print('x:' + str(x) + ' y:' + str(y))

                if (x == 3):
                    pass
                # [[NW, NE], [SW, SE]]
                err_x = np.zeros((2, 2), float)

                err_y = np.zeros((2, 2), float)

                # NW data
                if (x > 0) and (y > 0):
                    err_x[0, 0] = Xtilt_error[y - 1, x - 1]
                    err_y[0, 0] = Ytilt_error[y - 1, x - 1]

                # NE data
                if (x < size_x - 1) and (y > 0):
                    err_x[0, 1] = Xtilt_error[y - 1, x]
                    err_y[0, 1] = Ytilt_error[y - 1, x]

                # SE data
                if (x > 0) and (y < size_y - 1):
                    err_x[1, 0] = Xtilt_error[y, x - 1]
                    err_y[1, 0] = Ytilt_error[y, x - 1]

                # SW data
                if (x < size_x - 2) and (y < size_y - 1):
                    err_x[1, 1] = Xtilt_error[y, x]
                    err_y[1, 1] = Ytilt_error[y, x]

                pass

                # If the gradient error for X is positive on the W side and negative on the E side, the post must be too low
                # NW + SE - NE - SW
                adj_x = err_x[0, 0] + err_x[1, 0] - err_x[0, 1] - err_x[1, 1]
                # If the gradient error for Y is positive on the N side and negative on the S side, the post must be too low
                # NW + NE - SE - SW
                adj_y = err_y[0, 0] + err_y[0, 1] - err_y[1, 0] - err_y[1, 1]

                convergence = abs((adj_x + adj_y) / (size_x * size_y))

                Zheight_recreated[y, x] = Zheight_recreated[y, x] + ((adj_y + adj_x) * 0.25)

        progress_percent = (i / 1000) * 100
        progress_percent = round(progress_percent, 0)
        progress_percent = int(progress_percent)

        if progress_percent > last_progress:
            last_progress = progress_percent

            progress_callback.emit(progress_percent, 'Running Process 3 / 3 ...')

    Zheight_recreated = Zheight_recreated - np.mean(Zheight_recreated)

    Zheight_lowpass = Zheight_recreated

    structure_size = size_x * size_y
    lowpass_samples = (round(structure_size / 60))
    lowpass_samples = int(lowpass_samples)

    for i in range(lowpass_samples):
        Zheight_lowpass = blur(Zheight_lowpass, 1)

    Zheight_delta = np.subtract(Zheight_lowpass, Zheight_recreated)

    return Zheight_recreated, Zheight_lowpass, Zheight_delta