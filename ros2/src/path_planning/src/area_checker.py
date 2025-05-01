import math

threshold = 0.5
area = [(-1.205, -0.83), (0.41,-1.23),(1.65,-1.3),(2.2, 0.2),(2.42,1.53),(2.2,3.75),(1.31,4.13),(-0.94,4.31),(-1.55,3.06),(-1.7,1.62),(-0.375, 0.8),(0.5,1.94)]

def check_area(lastArea, SCNN_data, SCNN_state ):

    if SCNN_state == 1:
        x = SCNN_data[0]
        y = SCNN_data[1]
        for i in range(len(area)):
            area_x, area_y = area[i]
            distance_final_point = math.sqrt((x - area_x)**2 + (y - area_y)**2)
            if distance_final_point <= threshold:
                return i
    elif lastArea == 100:
        return 100
    elif lastArea == 11:
        return 5
    else:
        return lastArea+1
    