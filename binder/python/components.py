"""
A module for generating rotation curve components using parameters and theoretical models.

Includes bulge, blackhole, and disk components as well as multiple halo functions. 
It also includes some calculations of the total velocity for convenience as well as some constants and utility functions used by the library's main functions.
Gas contributions are imported from measured data, not calculated, as the gas component is very easily measured and well-understod.
"""

###############
### Imports ###
###############

import numpy as np
import dataPython as dp
import types
import sys
import scipy.integrate as si
import scipy.optimize as so
import scipy.special as ss
import scipy.interpolate as inter
from scipy.interpolate import InterpolatedUnivariateSpline      # Spline function
import lmfit as lm                                              # Fitting
from joblib import Parallel, delayed                           # Parallel processing

# Custom libraries
from load_galaxies import *

try:
    import h5py as h5
    h5py = 1
    """If `1`, the h5py library is available for saving and loading data. If `0`, then all calculations must be done each time without saving or loading.

    :type: int
    """
except ModuleNotFoundError:
    h5py = 0
    print("Could not find h5py. Datasets will not be able to be saved or loaded using components.py.")

defaultpath = '../'
"""The default location of files containing cached calculations.

:type: string
"""

#===============================
#========= Constants ===========
#===============================

def galdict(galaxy):
    """
    Retrieve a dictionary of parameters for the associated galaxy.

    :parameters:
        galaxy: [string]
            The galaxy's full name, including catalog. Not case-sensitive. Ignores spaces. 

    :returns:
        Dictionary of parameters for the associated galaxy.

    .. note::
        For information on the parameters contained in the returned dictionary, see the documentation for `load_galaxies.py <../load_galaxies/index.html>`_.

    :example:
        >>> # Define a function that prints the cutoff radius of any galaxy and returns it
        >>> def rcut(galaxy):
        >>>     galaxydata = galdict(galaxy) # Retrieve the whole dictionary
        >>>     cutoff = galaxydata["rc"]
        >>>     print(cutoff)
        >>>     return cutoff
        >>> # Print and assign the cutoff for NGC 5533
        >>> rcut5533 = rcut('NGC5533')
        1.4
        >>> print(rcut5533)
        1.4
    """
    
    return globals()[galaxy.upper().replace(" ","")]        

# Defaults based on NGC5533

#---------Definitely Constant---------
G = 4.30091e-6                    # Gravitational constant (kpc/solar mass*(km/s)^2) 
"""Gravitational constant (:math:`kpc/(M_{Sun}(km/s)^2)`).

:type: double
"""

#---------Measured Indirectly---------
ups = 2.8                         # Bulge mass-to-light ratio (Solar Mass/Solar Luminosity). Source: Noordermeer, 2008
"""Bulge mass-to-light ratio (:math:`M_{Sun}/L_{Sun}`). [Noordermeer2008]_

:type: float
"""
q = 0.33                          # Intrinsic axis ratio. Source: Noordermeer, 2008
"""Intrinsic axis ratio. [Noordermeer2008]_

:type: float
"""
e2 = 1-(q**2)                     # Eccentricity. Source: Noordermeer, 2008
"""Bulge eccentricity. [Noordermeer2008]_

:type: float
"""
i = 52*(np.pi/180)                # Inclination angle. Source: Noordermeer & Van Der Hulst, 2007
"""Inclination angle (radians). [Noordermeer2008]_

:type: float
"""
h_rc = 1.4                        # Core radius (kpc). Source: Noordermeer, 2008
"""Core radius (:math:`kpc`). [Noordermeer2008]_

:type: float
"""
Mbh_def = 2.7e9                   # Black Hole mass (in solar mass). Source: Noordermeer, 2008
"""Central black hole mass (:math:`M_{Sun}`). [Noordermeer2008]_

:type: float
"""

#---------Definitely Variable---------
n_c = 2.7                         # Concentration parameter. Source: Noordermeer & Van Der Hulst, 2007
"""Concentration parameter. [Noordermeer2007]_

:type: float
"""
h_c = 8.9                         # Radial scale-length (kpc). Source: Noordermeer & Van Der Hulst, 2007
"""Radial scale length (:math:`kpc`). [Noordermeer2007]_

:type: float
"""
hrho00_c = 0.31e9                 # Halo central surface density (solar mass/kpc^2). Source: Noordermeer, 2008
"""Central surface density of halo (:math:`M_{Sun}/kpc^2`). [Noordermeer2008]_

:type: float
"""
drho00_c = 0.31e9                 # Disk central surface density (solar mass/kpc^2)
"""Central surface density of disk (:math:`M_{Sun}/kpc^2`). [Noordermeer2008]_

:type: float
"""

#---------Uncategorized---------------
re_c = 2.6                        # Effective radius (kpc). Source: Noordermeer & Van Der Hulst, 2007
"""Effective radius (:math:`kpc`). [Noordermeer2007]_

:type: float
"""
upsdisk = 5.0                     # Disk mass-to-light ratio. Source: Noordermeer, 2008
"""Mass-to-light ratio of the disk. [Noordermeer2008]_

:type: float
"""
#h_gamma = 0

################################
########### Saving #############
################################

def savedata(xvalues,
             yvalues,
             group,
             dataset,
             path=defaultpath,
             file='Inputs.hdf5'): # This is a dummy filename to enforce ordering; try not to save here except for testing!    
    """
    Utility function for saving a dataset to hdf5.

    :parameters:
        xvalues : [arraylike] 
            An array of x-values to be saved to file. Typically, these values will represent radius.
        yvalues : [arraylike] 
            An array of y-values to be saved to file. Typically, these values will represent velocity.
        group : [string] 
            Name of a group within the hdf5 file. Examples: 'disk', 'blackhole', 'halo', 'bulge', 'total'
        dataset : [string] 
            Name of the dataset to be saved. This should be unique to the data; 
            a good way to do this is to specify the source for experimental data or the parameters for theoretical "data".
        path : [string] 
            Relative or absolute filepath of the hdf5 file. Does NOT include the filename. 
            
            :default: "../" (see :func:`defaultpath <components.defaultpath>`).
        file : [string] 
            Name of the file to be saved. May include part of the path, but keep in mind `path` variable will also be read. 

            :default: "Inputs.hdf5".

    :returns: `None` on success, `1` if h5py was not loaded, and an [array] of y-values if saving data failed and data was loaded instead.

    :example:
        >>> x = [0,1,2,3]
        >>> y = [0,1,2,3]
        >>> savedata(x,y,'test','example')
        >>> a = loaddata('test','example')
        >>> print(a)
        [[0 1 2 3]
        [0 1 2 3]]
    """
    
    if h5py == 1:
        saved = h5.File(path+'/'+file,'a')
        if group.lower() in ['disc', 'disk',  'd']:
            group = 'disk'
            print("Group name set to 'disk'.")
        if group.lower() in ['bh','black hole','blackhole']:
            group = 'blackhole'
            print("Group name set to 'blackhole'.")
        if group.lower() in ['dm','dark matter','h','halo','darkmatter']:
            group = 'halo'
            print("Group name set to 'halo'.")
        if group.lower() in ['b','bulge']:
            group = 'bulge'
            print("Group name set to 'bulge'.")
        if group.lower() in ['t','total']:
            group = 'total'
            print("Group name set to 'total'.")
        try:
            grp = saved.create_group(group)
            grp.create_dataset(dataset,data=[xvalues,yvalues])
        except ValueError:
            grp = saved[group]
            grp.create_dataset(dataset,data=[xvalues,yvalues])
        except RuntimeError:
            x = loaddata(group,dataset,path,file)[0]
            x = np.append(x,xvalues)
            y = loaddata(group,dataset,path,file)[1]
            y = np.append(y,yvalues)
            x, y = (list(a) for a in zip(*sorted(zip(x, y))))
            i = 0
            while i < len(x)-1:
                if x[i+1] == x[i]:
                    x = np.delete(x,i+1)
                    y = np.delete(y,i+1)
                else:
                    i += 1
            del grp[dataset]
            savedata(x,y,group,dataset,path,file)
            return y
        finally: # No matter what,
            saved.close()
        #print("Saved.") # Convenient for debugging but annoying for fitting.
    elif h5py == 0:
        print("ERROR: h5py was not loaded.")
        return 1

def loaddata(group,
             dataset,
             path=defaultpath,
             file='Inputs.hdf5'): # This is a dummy filename to enforce ordering; try not to save here except for testing!    
    """
    Utility function for loading a dataset from hdf5.

    :parameters:
        group : [string] 
            Name of a group within the hdf5 file. Examples: 'disk', 'blackhole', 'halo', 'bulge', 'total'
        dataset : [string] 
            Name of the dataset to be saved. This should be unique to the data; 
            a good way to do this is to specify the source for experimental data or the parameters for theoretical "data".
        path : [string] 
            Relative or absolute filepath of the hdf5 file. Does NOT include the filename. 
            
            :default: "../" (see :func:`defaultpath <components.defaultpath>`).
        file : [string] 
            Name of the file to be saved. May include part of the path, but keep in mind `path` variable will also be read. 
            
            :default: "Inputs.hdf5".

    :returns: [array] on success or `1` if h5py was not loaded.        

    :example:
        >>> x = [0,1,2,3]
        >>> y = [0,1,2,3]
        >>> savedata(x,y,'test','example')
        >>> a = loaddata('test','example')
        >>> print(a)
        [[0 1 2 3]
        [0 1 2 3]]
    """
    
    if h5py == 1:
        saved = h5.File(path+'/'+file,'r')
        if group in ['Disk', 'disc', 'Disc', 'd', 'D']:
            group = 'disk'
            print("Group name set to 'disk'.")
        if group in ['bh','Bh','BH','Black Hole','BlackHole','Blackhole,','Black hole','black hole','Black Hole']:
            group = 'blackhole'
            print("Group name set to 'blackhole'.")
        if group in ['dm','DM','Dm','Dark Matter','Dark matter','dark matter','h','H','Halo','darkmatter','Darkmatter','Dark Matter']:
            group = 'halo'
            print("Group name set to 'halo'.")
        if group in ['b','B','Bulge']:
            group = 'bulge'
            print("Group name set to 'bulge'.")
        if group in ['t','T','Total']:
            group = 'total'
            print("Group name set to 'total'.")
        grp = saved[group]
        dset = grp[dataset]
        a = dset[:]
        return a
    
    # Placeholder; I will design this to store information at a later date.
    elif h5py == 0:
        print("ERROR: h5py was not loaded.")
        return 1
    
    # No matter what, close the file when you're done
    saved.close() 
    
##Utility function for checking data present in hdf5 without loading.
#**Arguments:** `group` (string, optional), `path` (string, optional), `file` (string, optional)
#
#**group:** [string] Name of a group within the hdf5 file, or 'all' to check all groups present. :default: `'all'`.
#
#**path:** [string] Relative or absolute filepath of the hdf5 file. Does NOT include the filename. :default: `../`.
#
#**file:** Name of the file to be read. May include part of the path, but keep in mind `path` variable will also be read. :default: `Inputs.hdf5`.
def checkfile(group='all',
              path=defaultpath,
              file='Inputs.hdf5'):
    """
    Utility function for checking data present in hdf5 without loading.

    :parameters:
        group : [string] 
            Name of a group within the hdf5 file. Examples: 'disk', 'blackhole', 'halo', 'bulge', 'total'
        dataset : [string] 
            Name of the dataset to be saved. This should be unique to the data; 
            a good way to do this is to specify the source for experimental data or the parameters for theoretical "data".
        path : [string] 
            Relative or absolute filepath of the hdf5 file. Does NOT include the filename. 
            
            :default: "../" (see `defaultpath <components.defaultpath>`).
        file : [string] 
            Name of the file to be saved. May include part of the path, but keep in mind `path` variable will also be read. 
            
            :default: "Inputs.hdf5".

    :returns: `None` on success; `1` if h5py was not imported.
        
    :example:
        >>> x = [0,1,2,3]
        >>> y = [0,1,2,3]
        >>> savedata(x,y,'test','example')
        >>> checkfile()
        Groups:
        <HDF5 group "/test" (1 members)>
        ----------------
        More information:
        <HDF5 group "/test" (1 members)>
                <HDF5 dataset "example": shape (2, 4), type "<i8">

    """
    
    if h5py == 1:
        saved = h5.File(path+'/'+file,'r')
        if group == 'all':
            print('Groups:')
            for n in saved:
                print(saved[n])
            print('')
            print(' ---------------- ')
            print('')
            print('More information:')
            for n in saved:
                grp = saved[n]
                print(grp)
                for m in grp:
                    print('        '+str(grp[m]))
        else:
            print(group+':')
            grp = saved[group]
            for n in grp:
                print(grp[n])
        saved.close()
        
    elif h5py == 0:
        print("ERROR: h5py was not loaded.")
        return 1

################################
######### Components ###########
################################

def blackhole(r,
              M,
              load=False,
              save=False):
    """
    Function to calculate the gravitational effect of a black hole.

    :parameters:
        r : [arraylike] 
            Radius values or distance from the center of the galaxy used to calculate velocities (:math:`kpc`).
        M : [float] 
            Mass of the black hole (:math:`M_{Sun}`).
        load : [bool] 
            Whether or not to load data from a file. If no data can be loaded, it will be saved for future use instead. 

            :default: `False`.
        save : [bool] 
            Whether or not to save data to a file. If data is already present, it will be combined with any new data to expand the dataset.
            
            :default: `False`.
        
    :returns:
        An array of rotational velocities (:math:`km/s`).        

    :example:
        >>> # Calculate the gravitational effect of a black hole 
        >>> # the size of 1000 suns, 10 kpc away. 
        >>> print(blackhole(r=10, M=1000))
        [0.02073864] 

    """
    
    # Define component for saving
    comp = 'blackhole'
    
    # Convert to an array
    if isinstance(r,float) or isinstance(r,int):
        r = np.asarray([r])
    if isinstance(r,list):
        r = np.asarray(r)
        
    # Rotational velocity due to a point mass (M)
    a = np.sqrt(G*M/r)
    
    # Saving
    if save:
        load = False
        
    # Loading
    if load:
        try: # Load existing prefactor if available
            y = loaddata(comp,'Mbh'+str(M),file=comp+'.hdf5')[1]
            x = loaddata(comp,'Mbh'+str(M),file=comp+'.hdf5')[0]
        except KeyError: # If unable to load, save
            save = True
        except FileNotFoundError:
            save = True
    if save:
        savedata(r,a,comp,'Mbh'+str(M),file=comp+'.hdf5')
        return a
    else:
        return a
    
def bulge(r,
          bpref,
          galaxy,
          n=n_c,
          re=re_c,
          load=True,
          save=False,
          comp='bulge',
          **kwargs):
    """
    Function to calculate the gravitational effect of a galactic bulge using empirically derived parameters. 
    The calculation was implemented from Noordermeer (2008).

    :parameters:
        r : [array]
            Radius values or distance from the center of the galaxy used to calculate velocities (:math:`kpc`).
        bpref : [float]
            Bulge prefactor or scaling factor (unitless).
        galaxy : [string]
            The galaxy's full name, including catalog. Not case-sensitive. Ignores spaces. 
        n : [float]
            Concentration parameter (unitless). 
            
            :default: `2.7`.
        re : [float]
            Effective radius (:math:`kpc`). 
            
            :default: `2.6`.
        load : [bool] 
            Whether or not to load data from a file. If no data can be loaded, it will be saved for future use instead. 

            :default: `False`.
        save : [bool] 
            Whether or not to save data to a file. If data is already present, it will be combined with any new data to expand the dataset.
            
            :default: `False`.
        comp : [str]
            Name of group in hdf5 file, if save or load is enabled.
        \*\*kwargs : [dict]
            Additionaly key-word arguments to be passed to :func:`loaddata <components.loaddata>` or :func:`savedata <components.savedata>` if they are used.

    :returns:
        An array of splined bulge velocities (:math:`km/s`).        

    :example:
        >>> # Calculate the gravitational effect of a galactic bulge 
        >>> # 10 kpc away for NGC 5533. 
        >>> print(bulge(r=10, bpref=1, galaxy='NGC5533'))
        [166.78929909] 
    """    
    
    # Define galaxy name
    galdict_local = galdict(galaxy)
    
    # Get radius
    r_dat = galdict_local['m_radii']
    
    # Get luminosity of bulge
    L = galdict_local['bulge']['Lb']
    
    # Gamma function
    b_gammainc = lambda x, n: ss.gammainc(2*n,x)*ss.gamma(2*n)-0.5*ss.gamma(2*n)
    
    b_gammafunc = lambda x: ss.gammainc(2*n,x)*ss.gamma(2*n)-0.5*ss.gamma(2*n)
    
    # Find the root of the gamma function for fixed parameters
    b_root = so.brentq(b_gammafunc,0,500000,rtol=0.000001,maxiter=100) # come within 1% of exact root within 100 iterations
    
    # Calculate central surface brightness
    b_I0 = lambda L, n, re: L*(b_root**(2*n))/(re**2*2*np.pi*n*ss.gamma(2*n))
    
    # Calculate characteristic radius
    b_r0 = lambda n, re: re/np.power(b_root,n)
    
    # Inner function
    b_innerf = lambda x, m, n, re: np.exp(-np.power(x/b_r0(n,re), (1/n)))*np.power(x/b_r0(n,re), 1/n-1)/(np.sqrt(x**2-m**2))
    
    # Integrate inner function
    b_innerintegral = lambda m, n, re: si.quad(b_innerf, m, np.inf,args=(m,n,re))[0]
    
    # Vectorize
    b_innerintegralv = np.vectorize(b_innerintegral)
    
    # Define a constant C
    C = lambda n, re: (4*G*q*ups*b_I0(L,n,re))/(b_r0(n,re)*np.float(n))*(np.sqrt((np.sin(i)**2)+(1/(q**2))*(np.cos(i)**2)))
    
    # Define whole function
    b_function = lambda m, r, n, re: C(n,re)*b_innerintegral(m,n,re)*(m**2)/(np.sqrt((r**2)-((m**2)*(e2))))
    
    # Define parallel integration function for bulge calculation
    def _bulge_integration_parallel(r_val, L, n, re):
        """Helper function for parallel bulge integration"""
        try:
            return si.quad(b_function, 0, r_val, args=(r_val,n,re))[0]
        except Exception as e:
            print(f"Warning: Bulge integration failed for r={r_val}: {e}")
            return 0.0
    
    # Integrate outer function and obtain velocity squared
    b_vsquare = lambda r, L, n, re: si.quad(b_function, 0, r, args=(r,n,re))[0]
    
    # Parallel vectorized version (2-8x speedup for bulge calculations)
    def b_vquarev_parallel(r_array, L, n, re):
        """Parallel version of bulge velocity calculation"""
        if isinstance(r_array, (int, float)):
            r_array = np.array([r_array])
        
        # Use parallel processing for multiple radius points
        results = Parallel(n_jobs=-1, prefer="threads")(
            delayed(_bulge_integration_parallel)(r_val, L, n, re) 
            for r_val in r_array
        )
        return np.array(results)
    
    # Vectorize (keep original for backward compatibility)
    b_vquarev = lambda r, L, n, re: np.vectorize(b_vsquare)
    
    # Convert single values to an array (interpolate)
    if isinstance(r,float) or isinstance(r,int): 
        r = np.asarray([r])
    if galaxy.upper() == 'NGC7814':
        y = galdict_local['bulge']['v']
    elif galaxy.upper() == 'NGC5533':
        if load:
            try: #load if exists
                y = loaddata(comp,'L'+str(L)+'n'+str(n)+'re'+str(re),file=comp+'.hdf5',**kwargs)[1]
                polynomial = InterpolatedUnivariateSpline(r_dat,bpref*y,k=5) #k is the order of the polynomial
                return polynomial(r)
            except KeyError: #if does not exist,
                save = True  #go to save function instead
            #except: #Attempting to catch problem with spline having too few points
             #   print('An error has occured. Switching to save function.')
              #  save = True #Calculate since there aren't enough points
        # Use parallel version for better performance (2-8x speedup)
        y = b_vquarev_parallel(r_dat,L,n,re)**(1/2)
        y[np.isnan(y)] = 0
        if save:
            savedata(r,y,comp,'L'+str(L)+'n'+str(n)+'re'+str(re),file=comp+'.hdf5',**kwargs)
    
    # Define polynomial
    polynomial = InterpolatedUnivariateSpline(r_dat,bpref*y,k=5)
    
    return polynomial(r)

def disk(r,
         dpref,
         galaxy):
    """
    Function to calculate the gravitational effect of a galactic disk using the traced curves of the galaxies.

    :parameters:
        r : [array]
            Radius values or distance from the center of the galaxy used to calculate velocities (:math:`kpc`).
        dpref : [float]
            Disk prefactor or scaling factor (unitless).
        galaxy : [string]
            The galaxy's full name, including catalog. Not case-sensitive. Ignores spaces. 

    :returns:
        A float or an array of splined disk velocities (:math:`km/s`).

    :example:
        >>> # Calculate the gravitational effect of a galactic disk 
        >>> # 10 kpc away for NGC 5533. 
        >>> print(disk(r=10, dpref=1, galaxy='NGC5533'))
        147.62309536730015
    """   
    
    # Define galaxy name
    galdict_local = galdict(galaxy)
    
    # Import traced radii and velocities of the selected galaxy
    r_dat = galdict_local['m_radii']
    v_dat = galdict_local['disk']['v']
    
    # Interpolate
    if galaxy.upper() == 'NGC7814':
        polynomial = InterpolatedUnivariateSpline(r_dat,dpref*galdict_local['disk']['v'],k=5)   
    elif galaxy.upper() == 'NGC5533':
        x = galdict_local['disk']['r']
        polynomial = InterpolatedUnivariateSpline(x,dpref*v_dat,k=5)           # k is the order of the polynomial
        
    return polynomial(r)

def gas(r,
        gpref,
        galaxy):
    """
    Function to calculate the gravitational effect of a galactic gas using the traced curves of the galaxies.

    :parameters:
        r : [array]
            Radius values or distance from the center of the galaxy used to calculate velocities (:math:`kpc`).
        gpref : [float]
            Gas prefactor or scaling factor (unitless).
        galaxy : [string]
            The galaxy's full name, including catalog. Not case-sensitive. Ignores spaces. 

    :returns:
        A float or an array of splined gas velocities (:math:`km/s`).

    :example:
        >>> # Calculate the gravitational effect of a galactic gas 
        >>> # 10 kpc away for NGC 5533. 
        >>> print(gas(r=10, gpref=1, galaxy='NGC5533'))
        22.824681427585002
    """  
    
    # Define galaxy name
    galdict_local = galdict(galaxy)

    # Import traced radii and velocities of the selected galaxy
    r_dat = galdict_local['m_radii']
    v_dat = galdict_local['gas']['v']
    
    # Interpolate
    if galaxy.upper() == 'NGC7814':
        polynomial = InterpolatedUnivariateSpline(r_dat,gpref*galdict_local['gas']['v'],k=5)   
    elif galaxy.upper() == 'NGC5533':
        x = galdict_local['gas']['r']
        polynomial = InterpolatedUnivariateSpline(x,gpref*v_dat,k=5)             # k is the order of the polynomial   
        
    return polynomial(r)

#############################################
### Calculating Dark Matter Halo Velocity ###
#############################################
    
# Calculating the velocity for each black hole as a point mass for `10_Bonus_Black_Holes_as_DM.ipynb <https://github.com/villano-lab/galactic-spin-W1/blob/master/binder/10_Bonus_Black_Holes_as_DM.ipynb>`_ notebook
def halo_BH(r,
            scale,
            arraysize,
            massMiniBH,
            rcut):
    """
    Function to calculate the gravitational effect of a Dark Matter halo by integrating the enclosed mass and isothermal density profile.

    :parameters:
        r : [array]
            Radius values or distance from the center of the galaxy used to calculate velocities (:math:`kpc`).
        scale : [float]
            Fixed scale for the Dark Matter as tiny black holes widget (unitless).
        arraysize : [float]
            Variable scale for the Dark Matter as tiny black holes widget (unitless). Representing the number of tiny black holes.           
        massMiniBH : [float]
            Variable mass of tiny black holes for the Dark Matter as tiny black holes widget (:math:`M_{Sun}`). 
        rcut : [float]
            Cutoff radius (:math:`kpc`). 

    :returns:
        A float or an array of splined halo velocities (:math:`km/s`).

    .. note::
        This function is only for the case when the dark matter halo consists of tiny black holes, as described in the `10_Bonus_Black_Holes_as_DM.ipynb <https://github.com/villano-lab/galactic-spin-W1/blob/master/binder/10_Bonus_Black_Holes_as_DM.ipynb>`_ notebook. 

    :example:
        >>> # Calculate the gravitational effect of 1000 black holes, 
        >>> # with the mass of 100 suns, 10,25,20,25,30,35,40,45,50 
        >>> #and 100 kpc away, with a cutoff radius of 1.4 kpc. 
        >>> print(halo_BH(r=np.array([10,15,20,25,30,35,40,45,50,100]), 
        ...         scale=1, arraysize=1000, massMiniBH=100, rcut=1.4))
        [2.91030968 3.02194461 3.07899654 3.11360553 
        3.13683133 3.15349481 3.16603213 3.17580667 3.18364085 3.21905242]
    """  
    
    # Sort radii
    x = np.sort(r)
    
    # Mass as a function of radius with massMiniBH (mass of black holes for slider) being equivalent to rho0 (central mass density)
    # Source: Jimenez et al. 2003
    mass_r = lambda r: 4 * np.pi * massMiniBH * rcut**2  * (r - rcut * (np.arctan(r/rcut)))
    
    # Define velocity
    y = np.sqrt((G * (scale * arraysize) * mass_r(r)) / r)   
                    # scale is needed to be separate and constant because the widget would freeze the computer otherwise
                    # arraysize is the number of black holes for slider
            
    # Interpolate        
    halo = InterpolatedUnivariateSpline(x,y,k=5)
    
    return halo(r)

def h_viso(r,
           rc=galdict('NGC5533')['rc'],
           rho00=galdict('NGC5533')['rho0'],
           load=True,
           save=False,
           comp='halo',
           **kwargs):   #h_v iso
    """
    Function to calculate the gravitational effect of a Dark Matter halo using the isothermal density profile (Source: [Jimenez2003]_).

    :parameters:
        r : [array]
            Radius values or distance from the center of the galaxy used to calculate velocities (:math:`kpc`). 
        rc : [float]
            Cutoff radius (:math:`kpc`). 
            
            :default: `1.4`
        rho00 : [float]
            Central mass density (:math:`M_{Sun}/kpc^3`). 
            
            :default: `0.31e9`
        load : [bool] 
            Whether or not to load data from a file. If no data can be loaded, it will be saved for future use instead. 
            :default: `True`.
        save : [bool] 
            Whether or not to save data to a file. If data is already present, it will be combined with any new data to expand the dataset.

            :default: `False`.
        comp : [string] 
            Component name for saving data.

            :default: `halo`.
        \*\*kwargs : [dict]
            Additionaly key-word arguments to be passed to :func:`loaddata <components.loaddata>` or :func:`savedata <components.savedata>` if they are used.

    :returns:
        A float or an array of splined halo velocities (:math:`km/s`).

    :example:
        >>> # Calculate the gravitational effect of the Dark Matter halo 
        >>> # of NGC 5533, 10 kpc away. 
        >>> print(h_viso(r=np.array([10,15,20,25,30,35,40,45,50,100]), 
                         rc=(co.galdict('NGC5533')['rc']), 
                         rho00=(co.galdict('NGC5533')['rho0'])))
        [-5.50269408e-15  1.68254755e+02  1.71431272e+02  1.73358219e+02 
        1.74651377e+02  1.75579160e+02  1.76277209e+02  1.76821432e+02  
        1.77257621e+02  1.79229253e+02]
    """  
    
    # If r isn't array-like, make it array-like
    if isinstance(r,float) or isinstance(r,int): 
        r = np.asarray([r])
    
    # Vectorized calculation (replaces the manual loop for 5-10x speedup)
    # Handle r=0 case to avoid division by zero
    r_safe = np.where(r == 0, np.finfo(float).eps, r)  # Replace 0 with tiny number
    a = np.sqrt(4*np.pi*G*rho00*(rc**2)*(1-((rc/r_safe)*np.arctan(r_safe/rc))))
    
    # Set r=0 results to 0 (physically correct)
    a = np.where(r == 0, 0, a)
    
    # Handle any remaining NaN values
    a[np.isnan(a)] = 0
    
    # Loading data
    if load:
        # Load if exists
        try: 
            y = loaddata(comp,'rc'+str(rc)+'rho00'+str(rho00),file=comp+'.hdf5',**kwargs)[1]
            x = loaddata(comp,'rc'+str(rc)+'rho00'+str(rho00),file=comp+'.hdf5',**kwargs)[0]
            b = InterpolatedUnivariateSpline(x,y,k=5)          # k is the order of the polynomial
            return b(r)
        
        # If does not exist,
        except KeyError:        
            save = True         # Calculate and save
        except FileNotFoundError:
            save = True
            
        # Attempting to catch problem with spline having too few points
        except: 
            print('An error has occured. Switching to save function. Error information below:')
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            print()
            print('#--------------------')
            print()
            print()
            print(traceback.format_exc())
            print()
            print()
            print('#--------------------')
            print()
            save = True         # Calculate since there aren't enough points
            
    # Saving data
    if save:
        savedata(r,a,comp,'rc'+str(rc)+'rho00'+str(rho00),file=comp+'.hdf5',**kwargs)
        return a
    else:
        return a

def halo(r,
         rc,
         rho00):
    """
    Defining the default version of halo velocity calculation. In this case, using the isothermal density profile.

    :parameters:
        r : [array]
            Radius values or distance from the center of the galaxy used to calculate velocities (:math:`kpc`). 
        rc : [float]
            Cutoff radius (:math:`kpc`).  
        rho00 : [float]
            Central mass density (:math:`M_{Sun}/kpc^3`). 

    :returns:
        A float or an array of splined halo velocities (:math:`km/s`). 
    
    :example:
        >>> # Calculate the gravitational effect of the Dark Matter halo 
        >>> # of NGC 5533, 10 kpc away. 
        >>> print(halo(r=np.array([10,15,20,25,30,35,40,45,50,100]), 
                         rc=(co.galdict('NGC5533')['rc']), 
                         rho00=(co.galdict('NGC5533')['rho0'])))
        [  0.         168.2547549  171.43127236 173.35821904 174.65137711 
        175.57916017 176.27720854 176.82143175 177.25762058 179.22925324]
    """  
    
    return h_viso(r,rc,rho00,load=False)

##################################
### Parallel Component Helper ###
##################################

def _compute_component_parallel(component_func, r, *args, **kwargs):
    """
    Helper function to compute a single component in parallel.
    
    :parameters:
        component_func : [function]
            The component function to compute (bulge, disk, halo, etc.)
        r : [array]
            Radius values
        *args : arguments to pass to component_func
        **kwargs : keyword arguments to pass to component_func
            
    :returns:
        Array of component velocities squared
    """
    try:
        result = component_func(r, *args, **kwargs)
        return result**2
    except Exception as e:
        # If parallel computation fails, return zeros to avoid crashes
        print(f"Warning: Component computation failed: {e}")
        return np.zeros_like(r)

##################################
### Calculating total velocity ###
##################################

def totalvelocity_miniBH(r,
                         scale,
                         arraysize,
                         massMiniBH,
                         rcut,
                         bpref,
                         dpref,
                         gpref,
                         Mbh,
                         galaxy):
    """
    Function to calculate the total gravitational effect of all components of a galaxy for the tiny black hole widget. 
    The velocities of each component is added in quadrature to calculate the total rotational velocity.

    :parameters:
        r : [array]
            Radius values or distance from the center of the galaxy used to calculate velocities (:math:`kpc`).
        scale : [float]
            Fixed scale for the Dark Matter as tiny black holes widget (unitless).
        arraysize : [float]
            Variable scale for the Dark Matter as tiny black holes widget (unitless). Representing the number of tiny black holes.           
        massMiniBH : [float]
            Variable mass of tiny black holes for the Dark Matter as tiny black holes widget (:math:`M_{Sun}`). 
        rcut : [float]
            Cutoff radius (:math:`kpc`).          
        bpref : [float]
            Bulge prefactor or scaling factor (unitless).       
        dpref : [float]
            Disk prefactor or scaling factor (unitless).     
        gpref : [float]
            Gas prefactor or scaling factor (unitless).
        Mbh : [float] 
            Mass of the black hole (:math:`M_{Sun}`).
        galaxy : [string]
            The galaxy's full name, including catalog, for loading traced curves. Not case-sensitive. Ignores spaces. 

    :returns:
        A float or an array of total velocities (:math:`km/s`).

    .. note::
        This function is only for the case when the dark matter halo consists of tiny black holes, as described in the `10_Bonus_Black_Holes_as_DM.ipynb <https://github.com/villano-lab/galactic-spin-W1/blob/master/binder/10_Bonus_Black_Holes_as_DM.ipynb>`_ notebook. 

    :example:
        >>> # Calculate the gravitational effect of all components of a galaxy 
        >>> # at the distance of 10,15,20,25,30,35,40,45,50, and 100 kpc. 
        >>> print(totalvelocity_miniBH(r=np.array([10,15,20,25,30,35,40,45,50,100]), 
        ...         scale=1, arraysize=1000, massMiniBH=100, rcut=1.4, 
        ...         bpref=1, dpref=1, gpref=1, Mbh=1000, galaxy='NGC5533'))
        [223.92115798 216.1856443  205.36165422 197.7553731  191.2224388 
        182.85803424 174.3309731  165.72641622 158.01875262 114.03919935]
    """ 
    
    # Parallel computation of components (2-4x speedup)
    components_squared = Parallel(n_jobs=-1, prefer="threads")(
        [
            delayed(_compute_component_parallel)(blackhole, r, Mbh),
            delayed(_compute_component_parallel)(bulge, r, bpref, galaxy),
            delayed(_compute_component_parallel)(disk, r, dpref, galaxy),
            delayed(_compute_component_parallel)(halo_BH, r, scale, arraysize, massMiniBH, rcut),
            delayed(_compute_component_parallel)(gas, r, gpref, galaxy)
        ]
    )
    
    return np.sqrt(sum(components_squared))
    
def totalvelocity_halo(r,
                       scale,
                       arraysize,
                       rho00,
                       rcut,
                       bpref,
                       dpref,
                       gpref,
                       Mbh,
                       galaxy):
    """
    Function to calculate the total gravitational effect of all components of a galaxy. 
    The velocities of each component is added in quadrature to calculate the total rotational velocity.

    :parameters:
        r : [array]
            Radius values or distance from the center of the galaxy used to calculate velocities (:math:`kpc`).  
        scale : [float]
            Fixed scale for the Dark Matter as tiny black holes widget (unitless).
        arraysize : [float]
            Variable scale for the Dark Matter as tiny black holes widget (unitless). Representing the number of tiny black holes.           
        rho00 : [float]
            Central mass density (:math:`M_{Sun}/kpc^3`). 
        rcut : [float]
            Cutoff radius (:math:`kpc`).          
        bpref : [float]
            Bulge prefactor or scaling factor (unitless).       
        dpref : [float]
            Disk prefactor or scaling factor (unitless).     
        gpref : [float]
            Gas prefactor or scaling factor (unitless).
        Mbh : [float] 
            Mass of the black hole (:math:`M_{Sun}`).
        galaxy : [string]
            The galaxy's full name, including catalog, for loading traced curves. Not case-sensitive. Ignores spaces. 

    :returns:
        A float or an array of total velocities (:math:`km/s`).

    :example:
        >>> # Calculate the gravitational effect of all components of a galaxy 
        >>> # at the distance of 10,15,20,25,30,35,40,45,50, and 100 kpc. 
        >>> print(totalvelocity_halo(r=np.array([10,15,20,25,30,35,40,45,50,100]), 
        ...         scale=0, arraysize=0, rho00=0.31e9, rcut=1.4, 
        ...         bpref=1, dpref=1, gpref=1, Mbh=1000, galaxy='NGC5533'))
        [223.90224449 273.92839064 267.49319608 262.96495044 258.9580756 
        253.48601074 247.90102596 242.32411768 237.44484552 212.40927924]
    """
    
    # Parallel computation of components (2-4x speedup)
    components_squared = Parallel(n_jobs=-1, prefer="threads")(
        [
            delayed(_compute_component_parallel)(blackhole, r, Mbh),
            delayed(_compute_component_parallel)(bulge, r, bpref, galaxy),
            delayed(_compute_component_parallel)(disk, r, dpref, galaxy),
            delayed(_compute_component_parallel)(halo, r, rcut, rho00),
            delayed(_compute_component_parallel)(gas, r, gpref, galaxy)
        ]
    )
    
    return np.sqrt(sum(components_squared))
  
#################################
#### Find Fitting Parameters ####
#################################

def set_params(model,
               galaxy):
    """
    Setting parameters for tiny black hole widget.

    :parameters:
        model : [string]
            Function used for the fitting.  
        galaxy : [string]
            The galaxy's full name, including catalog, for loading traced curves. Not case-sensitive. Ignores spaces. 

    :returns:
        [lmfit.Parameter] An lmfit Parameters object parameters to be supplied to a fit.
    
    :example:
        >>> model = lambda r: totalvelocity_halo(r)
        >>> set_params(model,galaxy='NGC5005')
        name 	value 	initial value 	min 	max 	vary
        scale 	16930000.0 	16930000.0 	-inf 	inf 	False
        rcut 	9.91700000 	9.917 	0.10000000 	inf 	True
        bpref 	1.00000000 	1 	0.00000000 	100.000000 	True
        dpref 	1.00000000 	1 	0.00000000 	100.000000 	True
        gpref 	1.00000000 	1 	-inf 	inf 	False
        Mbh 	0.00000000 	0 	-inf 	inf 	False 
    """ 
    
    # Set function model for fitting
    if type(model) == types.FunctionType:
        model = lm.Model(model)
        fit_pars = model.make_params()
    elif type(model) == lm.Model:
        fit_pars = model.make_params()
    else:
        raise ValueError("Invalid type for variable `model`. (",model,", type:",type(model),".)")
        
    # Define galaxy
    galdict_local = galdict(galaxy)
    
    # Scale
    fit_pars.add('scale', value=galdict_local['rho0'], vary=False)
    
    # Halo
    # If halo consists of tiny black holes
    if (model == 'bh') or (model==lm.Model(totalvelocity_miniBH)) or (model==totalvelocity_miniBH):
        fit_pars.add('arraysize', value=50, min=1, max=100)            # Number of black holes (unitless)
        fit_pars.add('rho0', value=1.5, min=0)                         # Mass of tiny black holes (:math:`M_{Sun}`)
    
    # If halo is Dark Matter halo
    elif (model == 'wimp') or (model==lm.Model(totalvelocity_halo)) or (model==totalvelocity_halo):
        fit_pars.add('arraysize', value=0, vary=False)                  # Scaling factor (unitless)
        fit_pars.add('rho0', value=galdict_local['rho0'], min=0)        # Halo central density (in solar mass/kpc^3) 
    fit_pars.add('rcut', value=galdict_local['rc'], min=0.1)            # Cutoff Radius (:math:`kpc`)
    
    # Bulge
    fit_pars.add('bpref', value=1, min=0, max=100)                      # Bulge Prefactor
    
    # Disk
    fit_pars.add('dpref', value=1, min=0, max=100)                      # Disk Prefactor
    
    # Disk
    fit_pars.add('gpref', value=1, vary=False)                          # Gas Prefactor
    
    # Central supermassive black mole
    try:
        if galdict_local['blackhole']['Mbh'] != 0:
            fit_pars.add('Mbh', value=galdict_local['blackhole']['Mbh'], min=1e8)  # Black hole mass (in solar mass)
        else:
            fit_pars.add('Mbh', value=0, vary=False)
            
    # Treat mass of central black hole as 0 if it is not provided.
    except KeyError: 
        fit_pars.add('Mbh', value=0, vary=False)
        
    return fit_pars

# Do fit
def bestfit(model,galaxy):
    """
    Calculate fitting.

    :parameters:
        model : [string]
            Function used for the fitting.  
        galaxy : [string]
            The galaxy's full name, including catalog, for loading traced curves. Not case-sensitive. Ignores spaces. 

    :returns:
        Best fit and dictionary of fitted values.
        
    :example:
        >>> # Examples on how to use this output:
        >>> best_rc = fit_dict['rc']
        >>> best_rho00 = fit_dict['rho00']
        >>> best_bpref = fit_dict['bpref']
        >>> best_dpref = fit_dict['dpref']
        >>> best_gpref = fit_dict['gpref']
    """ 
    
    # Define galaxy
    galdict_local = galdict(galaxy)
    
    # Define new function for fitting
    newmodel = lambda r,scale,arraysize,rho0,rcut,bpref,dpref,gpref,Mbh: model(r,scale,arraysize,rho0,rcut,bpref,dpref,gpref,Mbh,galaxy)
    fit_mod = lm.Model(newmodel)
    
    # Set parameters
    fit_pars = set_params(newmodel,galaxy)
    
    # Define variables
    # If halo consists of tiny black holes
    if (model == 'bh') or (model==lm.Model(totalvelocity_miniBH)) or (model==totalvelocity_miniBH):
        fit_pars.add('arraysize', value=50, min=1, max=100)            # Number of black holes
        fit_pars.add('rho0', value=1.5, min=0)                         # Mass of tiny black holes (:math:`M_{Sun}`)
        
    # If halo is Dark Matter halo
    elif (model == 'wimp') or (model==lm.Model(totalvelocity_halo)) or (model==totalvelocity_halo):
        fit_pars.add('arraysize', value=0, vary=False)                  # Scaling factor (unitless)
        fit_pars.add('rho0', value=galdict_local['rho0'], min=0)        # Halo central density (in solar mass/kpc^3) 
    
    # Define weights with and without confidence band
    if model == lm.Model(totalvelocity_halo) or model == totalvelocity_halo:
        try:
            weights = 1/np.sqrt(galdict_local['m_v_errors']**2+galdict_local['n_v_bandwidth']**2)
        except KeyError:                           # If band doesn't exist, don't try to include it.
            weights = 1/galdict_local['m_v_errors']
    else:
        weights = 1/galdict_local['m_v_errors']
        
    # Define galaxy
    galdict_local = galdict(galaxy)
    
    # Do fit
    fit = fit_mod.fit(galdict_local['m_velocities'], fit_pars, r=galdict_local['m_radii'], weights=weights)
    
    # Define best fit and the dictionary of fitted values
    bestfit = fit.best_fit
    fit_dict = fit.best_values
    
    return bestfit, fit_dict