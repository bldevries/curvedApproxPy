import random
import os
import pickle
import numpy as np
import curvedpy as cp
from curvedpy.geodesics.blackhole import BlackholeGeodesicIntegrator

from curvedpy.utils.lpn_coordinates import angle, create_quat
from curvedpy.utils.lpn_coordinates import impact_vector_2 as impact_vector

from scipy.interpolate import RegularGridInterpolator



def curve_props(k, x, last_index = -1):
    """Calculate impact properties and angle of deflection from curvedpy geodesics

        Keyword arguments:
        k -- np.array containing spatial components of the 4momenta of geodesic points 
        x -- np.array containing spatial components of the 4position of a geodesic
        last_index --   optional index pointing to the last point to use from the k 
                        array to calculate the deflection (default -1)
    """
    x = np.column_stack(x)
    k = np.column_stack(k)
    
    ray_origin, ray_direction, ray_dir_end = x[0], k[0], k[last_index]

    ray_origin, ray_direction = np.array([ray_origin]), np.array([ray_direction])
    ray_dir_end = np.array([ray_dir_end])

    dTh = angle(ray_direction, ray_dir_end)
    print("WHAAAA", ray_origin.shape, ray_direction.shape)
    p, l, p_, l_ = impact_vector(ray_origin, ray_direction)

    # The angle between two vectors is ambiguous. This means arccos always picks
    # out the smallest angle between two vectors and the angle will never be bigger than 
    # pi. But we want the angle between the vector up to 2pi. Now if the angle between 
    # the start and end vector is larger than pi, we reverse the direction of theta
    # in order to get the proper rotation matrix out.
    if ray_dir_end.dot(p_[0]) >= 0.0:
        dTh= -dTh
    
    return dTh, p, l, p_, l_

def generate_data_file(save = True, save_directory = ".", add_str_to_filename= "", num=100, \
                        p = [0,200], l = [-200,200], adapt_grid=False,\
                        coordinates="SPH", m=1.0, max_step=0.1, R_end = 300., verbose=False):

    bi = cp.BlackholeGeodesicIntegrator(mass = m, coordinates=coordinates)

    p_start, p_end = p
    l_start, l_end = l

    R_sch = 2*m

    l_l = np.linspace(l_start, l_end, num)
    if adapt_grid:
        p_split = 5*R_sch
        l_p_part1 = np.linspace(p_start, R_sch, int(num/10))
        l_p_part2 = np.linspace(R_sch+0.01, p_split, num)
        l_p_part3 = np.linspace(p_split+0.01, p_end, int(num))

        l_p = np.concat([l_p_part1, l_p_part2, l_p_part3])
    else:
        l_p = np.linspace(p_start, p_end, num)
    

    th = np.zeros((l_p.shape[0],l_l.shape[0]))
    hit = np.zeros((l_p.shape[0],l_l.shape[0]))

    if verbose: print(f"Running {num=} {coordinates=} {m=} {max_step=} {R_end=} {verbose=}")

    for ip, y in enumerate(l_p):
        for il, x in enumerate(l_l):
            if verbose: print(ip, il, x, y)
            #for j in range(100):
            x0 = [-x, y, 0]
            k0 = [-1, 0, 0]
            R0 = np.linalg.norm(x0)

            if R0 > 2*m+0.1:
                k, x, _ = bi.geodesic(k0_xyz=k0, x0_xyz=x0, max_step=max_step, R_end = R_end)
                dTh, p, l, p_, l_ = curve_props(k, x)
                hit[ip, il] = _['hit_blackhole']
                th[ip, il] = dTh
            else:
                print("norun")
                hit[ip, il] = -1 # Start in BH

    filename = add_str_to_filename+\
        f"adaptgrid{adapt_grid}_num{num}_coord{coordinates}_m{m}_step{max_step}_Rend{R_end}_p{p_start}-{p_end}_l{l_start}-{l_end}"+\
        ".pkl"

    save_path = os.path.join(save_directory, filename)

    with open(save_path, 'wb') as f:
        pickle.dump([hit, th, l_p, l_l], f)

    return hit, th, l_p, l_l

def load_data_file(file_path, give_interpolate = True):
    if os.path.isfile(file_path):
        with open(file_path, 'rb') as f:
            hit, th, l_p, l_l = pickle.load(f)
            if give_interpolate:
                interp_hit, interp_th = create_interpolation(hit, th, l_p, l_l)
                return interp_hit, interp_th, [hit, th, l_p, l_l]
            else:
                return hit, th, l_p, l_l

def create_interpolation(hit, th, l_p, l_l):
    interp_hit = RegularGridInterpolator((l_p, l_l), hit)
    interp_th = RegularGridInterpolator((l_p, l_l), th)

    return interp_hit, interp_th












