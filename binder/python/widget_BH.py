"""A module for handling the black hole widgets found in `10_Bonus_Black_Holes_as_DM.ipynb <https://github.com/villano-lab/galactic-spin-W1/blob/master/binder/10_Bonus_Black_Holes_as_DM.ipynb>`_.
"""

#########################
### Black Hole Widget ###
#########################

###############
### Imports ###
###############

import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interactive, fixed, FloatSlider, HBox, Layout, Button, Label, Output, VBox
from IPython.display import display
import components as comp
import dataPython as dp

####################
### Galaxy image ###
####################

# Import galaxy image
img = plt.imread("images/A_spiral_snowflake.jpg")            # Import image of NGC 6814
"""An array of RGB data for a galaxy image (`images/A_spiral_snowflake.jpg`), imported using `matplotlib.pyplot.imread`.

:type: array
"""

# Find the center by eye from the image
center = [1960,1800]
"""Coordinate pair indicating the pixel location of the center of the galaxy in :func:`img <widget_BH.img>`.

:type: array
"""

# Kpc limits, visual guess based on the galaxy in the image chosen:
minkpc = 0
"""The minimum value (:math:`kpc`), allowed for the radial position of black holes on the plot.

:type: int
"""
maxkpc = 100
"""The maximum value (:math:`kpc`), allowed for the radial position of black holes on the plot.

:type: int
"""

##################
### Parameters ###
##################

# units: scale = [#number of actual black holes / plotted dot]
kpctopixels = 20                # visual scaling, varies depending on size of galaxy image (and actual size of galaxy)
"""Number of pixels per kpc for plotting black holes over black hole image.

:type: int
"""

# For mass of black hole slider:
minmassBH = 0.1                 # solar masses, arbitrary
"""The minimum value, in solar masses, allowed for the (average) black hole mass.

:type: float
"""
maxmassBH = 3.8                 # https://www.scientificamerican.com/gallery/the-smallest-known-black-hole/
"""The maximum value, in solar masses, allowed for the (average) black hole mass.

:type: float
"""
defaultmass = 1.5               # default mass value for slider
"""The default value, in solar masses, for the (average) black hole mass.

:type: float
"""
scale = 1e6                     # scale is neccessary to be a constant, otherwise the widget will freeze up the computer! 
"""The number of black holes represented by each dot in the galaxy plot.

:type: int
"""
# For number of black holes slider:
stepN = 5
"""The step size of the slider controlling the number of black holes. In terms of number of black holes represented, this step size is multiplied by the :func:`scale <widget_BH.scale>`.

:int:
"""

def minnumberBH(galaxy):
    """A function that returns the minimum number of black holes (prior to multiplying by the :func:`scale <widget_BH.scale>`) appropriate for the supplied galaxy.

    :parameters:
        galaxy : [string | int]
            The name or number (for NGC) of the selected galaxy. Names are not case-sensitive and ignore spaces. 
            Allowed inputs: "NGC5533" or "NGC7814".

    :returns: [int] 
        The minimum number of black holes, prior to multiplying by the :func:`scale <widget_BH.scale>`.
    
    .. seealso:: For an example usecase of this function, see :func:`arraysize_5533 <widget_BH.arraysize_5533>`.
    """
    if str(galaxy) == "5533" or str(galaxy).upper().replace(" ","") == 'NGC5533':
        return 50
    elif str(galaxy) == "7814" or str(galaxy).upper().replace(" ","") == 'NGC7814':
        return 1
    
def maxnumberBH(galaxy):
    """A function that returns the maximum number of black holes (prior to multiplying by the :func:`scale <widget_BH.scale>`) appropriate for the supplied galaxy.

    :parameters:
        galaxy : [string | int]
            The name or number (for NGC) of the selected galaxy. Names are not case-sensitive and ignore spaces. 
            Allowed inputs: "NGC5533" or "NGC7814".

    :returns: 
        [int] The maximum number of black holes, prior to multiplying by the :func:`scale <widget_BH.scale>`.
    
    .. seealso:: For an example usecase of this function, see :func:`arraysize_5533 <widget_BH.arraysize_5533>`.
    """
    if str(galaxy) == "5533" or str(galaxy).upper().replace(" ","") == 'NGC5533':
        return 5e2
    elif str(galaxy) == "7814" or str(galaxy).upper().replace(" ","") == 'NGC7814':
        return 1000
    
def defaultnumber(galaxy):
    """A function that returns the default number of black holes (prior to multiplying by the :func:`scale <widget_BH.scale>`) appropriate for the supplied galaxy.

    :parameters:
        galaxy : [string | int]
            The name or number (for NGC) of the selected galaxy. Names are not case-sensitive and ignore spaces. 
            Allowed inputs: "NGC5533" or "NGC7814".

    :returns: 
        [int] The default number of black holes, prior to multiplying by the :func:`scale <widget_BH.scale>`.
    
    .. seealso:: For an example usecase of this function, see :func:`arraysize_5533 <widget_BH.arraysize_5533>`.
    """
    if str(galaxy) == "5533" or str(galaxy).upper().replace(" ","") == 'NGC5533':
        return 245
    elif str(galaxy) == "7814" or str(galaxy).upper().replace(" ","") == 'NGC7814':
        return 600

#For cutoff radius:
minrcutBH = 0.1
"""The minimum cutoff radius for black holes (:math:`kpc`).

:type: float
"""

def maxrcutBH(galaxy):
    """A function that returns the maximum cutoff radius for black holes (:math:`kpc`), appropriate for the supplied galaxy.

    :parameters:
        galaxy : [string | int]
            The name or number (for NGC) of the selected galaxy. Names are not case-sensitive and ignore spaces. 
            Allowed inputs: "NGC5533" or "NGC7814".

    :returns: 
        [float] The maximum cutoff radius for black holes.
    
    .. seealso:: For an example usecase of this function, see :func:`arraysize_5533 <widget_BH.arraysize_5533>`.
    """
    if str(galaxy) == "5533" or str(galaxy).upper().replace(" ","") == 'NGC5533':
        return 3.0
    elif str(galaxy) == "7814" or str(galaxy).upper().replace(" ","") == 'NGC7814':
        return 4.0
    
def defaultrcutBH(galaxy):
    """A function that returns the default cutoff radius for black holes (:math:`kpc`), appropriate for the supplied galaxy.

    :parameters:
        galaxy : [string | int]
            The name or number (for NGC) of the selected galaxy. Names are not case-sensitive and ignore spaces. 
            Allowed inputs: "NGC5533" or "NGC7814".

    :returns: 
        [float] The default cutoff radius for black holes.
    
    .. seealso:: For an example usecase of this function, see :func:`arraysize_5533 <widget_BH.arraysize_5533>`.
    """
    if str(galaxy) == "5533" or str(galaxy).upper().replace(" ","") == 'NGC5533':
        return 1.4
    elif str(galaxy) == "7814" or str(galaxy).upper().replace(" ","") == 'NGC7814':
        return 1.6

    
style = {'description_width': 'initial'}
"""A dictionary for slider styling common to all sliders in this library.

:type: dict
"""

layout = {'width':'800px'}
"""A dictionary for slider layout commont to all sliders in this library.

:type: dict
"""

####################################
### Plotting function for widget ###
####################################

### NGC 5533 ###
def f5533(arraysize,massMiniBH,rcut):
    """
    Generate a plot of the NGC5533 data and components alongside an image of a galaxy with dots representing black holes.

    This function is intended for use as part of a widget.

    :parameters:
        arraysize: [int]
            Size intended for the radius and angle arrays.
        massMiniBH: [int]
            Mass of the tiny black holes, in solar masses.
        rcut: [float]
            Cutoff radius for black hole placement (:math:`kpc`).
    
    :returns: 
        None

    .. seealso:: For an example usage of this function, see the notebook `10_Bonus_Black_Holes_as_DM.ipynb on Binder <https://mybinder.org/v2/gh/villano-lab/galactic-spin-W1/HEAD?labpath=binder%2F10_Bonus_Black_Holes_as_DM.ipynb>`_.
    """
    _,fit_dict = comp.bestfit(comp.totalvelocity_miniBH,'NGC5533')
    
    bpref = fit_dict['bpref']
    dpref = fit_dict['dpref']
    gpref = fit_dict['gpref']
    Mbh = fit_dict['Mbh']
    
    # Define radius
    r = np.linspace(
        np.min(comp.galdict('NGC5533')['m_radii']), 
        np.max(comp.galdict('NGC5533')['m_radii']),500)
    
    # Change input to an integer
    arraysize = int(arraysize)     # units: dot
    
    # Random radii for the galaxy image
    # Trim to the first x elements (arraysize) of the pre-calculated radius arrays for each bracket
    rand_radius_5533 = lambda rad1,rad2: np.random.uniform(rad1,rad2,int(maxnumberBH(5533)))
    radius_trim = rand_radius_5533(minkpc*kpctopixels,maxkpc*kpctopixels)[:arraysize]
    rand_angle_5533 = np.random.uniform(0,2*np.pi,int(maxnumberBH(5533)))  # angle 0 to 360 degrees for full circle (donut) for each bracket
    angle_trim = rand_angle_5533[:arraysize]
    
    # x and y coordinates for plotting
    x = center[0] + radius_trim*np.cos(angle_trim)     # x coordinates
    y = center[1] + radius_trim*np.sin(angle_trim)     # y coordinates
    
    # Random radii for the plot
    radius_plot = rand_radius_5533(minkpc,maxkpc)[:arraysize]
    radius_plot = np.sort(radius_plot)           # sort array
    radius_plot[0] = 0.2    # first element of the radius should be close to zero because spline function won't plot up to zero
      
    # Set up two plots next to each other
    f, (ax1, ax2) = plt.subplots(1, 2, sharey=False)
    plt.subplots_adjust(wspace=0, hspace=0)
    f.set_figheight(12)
    f.set_figwidth(32)
    
    # Changing the size of each dot as the mass of the black hole changes
    # Without this the dots would be either too small or too big  
    dotsize = np.linspace(5,12,int(maxmassBH/minmassBH + 1))            # array of sizes from 5 to 12 for dots in scatterplot
    mass = np.round(np.arange(minmassBH,maxmassBH+minmassBH,minmassBH),1)   # array of masses, rounded to 1 decimal
    loc = np.where(mass == massMiniBH)[0]                           # which element equals to the mBH value, returns position
    BHsize = dotsize[loc[0]]                                        # picks out a dotsize for that mass
    
    # First plot - image with black holes
    ax1.plot(x,y, linestyle='none', markerfacecolor='orangered', marker="o", markeredgecolor="maroon", markersize=BHsize)
    ax1.imshow(img)
    ax1.set_title("Each dot representing 1 million tiny black holes.", fontsize=25)
    ax1.set_xlim(0,3970)
    ax1.set_ylim(0,3970)
    ax1.axis('off')
    
    # Second plot - rotation curve   
    ax2.plot(r,comp.halo_BH(r,scale,arraysize,massMiniBH,rcut),
             label=("Dark Matter Halo - Tiny Black Holes"),color='green')
    ax2.errorbar(comp.galdict('NGC5533')['m_radii'],comp.galdict('NGC5533')['m_velocities'],
                 yerr=comp.galdict('NGC5533')['m_v_errors'],fmt='bo',label='Data')
    ax2.plot(r,comp.blackhole(r,Mbh,'NGC5533'),label=("Central Black Hole"),color='black')
    ax2.plot(r,comp.bulge(r,bpref,'NGC5533'),label=("Bulge"),color='orange')
    ax2.plot(r,comp.disk(r,dpref,'NGC5533'),label=("Disk"),color='purple')
    ax2.plot(r,comp.gas(r,gpref,'NGC5533'),label=("Gas"),color='blue')
    ax2.plot(r,comp.totalvelocity_miniBH(r,scale,arraysize,massMiniBH,rcut,
                                  bpref,dpref,gpref,
                                  Mbh,'NGC5533'),label=("Total Curve"),color='red')
    ax2.set_title('NGC 5533',fontsize=40)
    ax2.set_ylabel('Velocity [km/s]',fontsize=25)
    ax2.set_xlabel('Radius [kpc]',fontsize=25)
    ax2.tick_params(axis='x', labelsize=16)
    ax2.tick_params(axis='y', labelsize=16)
    ax2.set_xlim(0,100)
    ax2.set_ylim(0,400)
    ax2.legend(bbox_to_anchor=(1,1), loc="upper left", fontsize=20) 

    # Residuals
    residuals = comp.galdict('NGC5533')['m_velocities'] 
    - comp.totalvelocity_miniBH(comp.galdict('NGC5533')['m_radii'],
                                scale,arraysize,massMiniBH,rcut,
                                                        bpref, dpref, gpref, Mbh,
                                                        'NGC5533')
    # Chi squared
    chisquared = np.sum(residuals**2/comp.galdict('NGC5533')['m_v_errors']**2)
    dof = len(comp.galdict('NGC5533')['m_radii']) - 6       # number of degrees of freedom = number of observed data - number of fitting parameters
    reducedchisquared = chisquared / dof
    
    props = dict(boxstyle='round', facecolor='white', alpha=0.5)
    ax2.text(98,390,r"Reduced $\chi^2$: {:.2f}".format(reducedchisquared),ha='right',va='top',bbox=props,size=22)
        
### NGC 7814 ###
def f7814(arraysize,massMiniBH,rcut):
    """
    Generate a plot of the NGC7814 data and components alongside an image of a galaxy with dots representing black holes.

    This function is intended for use as part of a widget.

    :parameters:
        arraysize: [int]
            Size intended for the radius and angle arrays.
        massMiniBH: [int]
            Mass of the tiny black holes, in solar masses.
        rcut: [float]
            Cutoff radius for black hole placement (:math:`kpc`).
    
    :returns: 
        None

    .. seealso:: For an example usage of this function, see the notebook `10_Bonus_Black_Holes_as_DM.ipynb on Binder <https://mybinder.org/v2/gh/villano-lab/galactic-spin-W1/HEAD?labpath=binder%2F10_Bonus_Black_Holes_as_DM.ipynb>`__.
    """
    _,fit_dict = comp.bestfit(comp.totalvelocity_miniBH,'NGC7814')
    
    bpref = fit_dict['bpref']
    dpref = fit_dict['dpref']
    gpref = fit_dict['gpref']
    
    # Define radius
    r = np.linspace(
        np.min(comp.galdict('NGC7814')['m_radii']),
        np.max(comp.galdict('NGC7814')['m_radii']),500)
    
    # Change input to an integer
    arraysize = int(arraysize)     # units: dot
    
    # Random radii for the galaxy image
    # Trim to the first x elements (arraysize) of the pre-calculated radius arrays for each bracket
    rand_radius_7814 = lambda rad1,rad2: np.random.uniform(rad1,rad2,int(maxnumberBH(7814)))
    radius_trim = rand_radius_7814(minkpc*kpctopixels,maxkpc*kpctopixels)[:arraysize]
    rand_angle_7814 = np.random.uniform(0,2*np.pi,int(maxnumberBH(7814)))  # angle 0 to 360 degrees for full circle (donut) for each bracket
    angle_trim = rand_angle_7814[:arraysize]
    
    # x and y coordinates for plotting
    x = center[0] + radius_trim*np.cos(angle_trim)     # x coordinates
    y = center[1] + radius_trim*np.sin(angle_trim)     # y coordinates
    
    # Random radii for the plot
    radius_plot = rand_radius_7814(minkpc,maxkpc)[:arraysize]
    radius_plot = np.sort(radius_plot)           # sort array
    radius_plot[0] = 0.2    # first element of the radius should be close to zero because spline function won't plot up to zero
      
    # Set up two plots next to each other
    f, (ax3, ax4) = plt.subplots(1, 2, sharey=False)
    plt.subplots_adjust(wspace=0, hspace=0)
    f.set_figheight(12)
    f.set_figwidth(32)
    
    # Changing the size of each dot as the mass of the black hole changes
    # Without this the dots would be either too small or too big  
    dotsize = np.linspace(5,12,int(maxmassBH/minmassBH + 1))            # array of sizes from 5 to 12 for dots in scatterplot
    mass = np.round(np.arange(minmassBH,maxmassBH+minmassBH,minmassBH),1)   # array of masses, rounded to 1 decimal
    loc = np.where(mass == massMiniBH)[0]                           # which element equals to the mBH value, returns position
    BHsize = dotsize[loc[0]]                                        # picks out a dotsize for that mass
    
    # First plot - image with black holes
    ax3.plot(x,y, linestyle='none', markerfacecolor='orangered', marker="o", 
             markeredgecolor="maroon", markersize=BHsize)
    ax3.imshow(img)
    ax3.set_title("Each dot representing 1 million tiny black holes.", fontsize=25)
    ax3.set_xlim(0,3970)
    ax3.set_ylim(0,3970)
    ax3.axis('off')
    
    # Second plot - rotation curve   
    ax4.plot(r,comp.halo_BH(r,scale,arraysize,massMiniBH,rcut),
             label=("Dark Matter Halo - Tiny Black Holes"),color='green')
    ax4.errorbar(comp.galdict('NGC7814')['m_radii'],
                 comp.galdict('NGC7814')['m_velocities'],yerr=comp.galdict('NGC7814')['m_v_errors'],fmt='bo',label='Data')
    ax4.plot(r,comp.bulge(r,bpref,'NGC7814'),label=("Bulge"),color='orange')
    ax4.plot(r,comp.disk(r,dpref,'NGC7814'),label=("Disk"),color='purple')
    ax4.plot(r,comp.gas(r,gpref,'NGC7814'),label=("Gas"),color='blue')
    ax4.plot(r,comp.totalvelocity_miniBH(r,scale,arraysize,massMiniBH,
                                                  rcut,bpref,dpref,
                                                  gpref,0,'NGC7814'),label=("Total Curve"),color='red')
    ax4.set_title('NGC 7814',fontsize=40)
    ax4.set_ylabel('Velocity [km/s]',fontsize=25)
    ax4.set_xlabel('Radius [kpc]',fontsize=25)
    ax4.tick_params(axis='x', labelsize=16)
    ax4.tick_params(axis='y', labelsize=16)
    ax4.set_xlim(0,np.max(comp.galdict('NGC7814')['m_radii']))
    ax4.set_ylim(0,400)
    ax4.legend(bbox_to_anchor=(1,1), loc="upper left", fontsize=20) 

    # Residuals
    residuals = comp.galdict('NGC7814')['m_velocities'] - comp.totalvelocity_miniBH(
        comp.galdict('NGC7814')['m_radii'], 
        scale,arraysize,massMiniBH,rcut, bpref, dpref, gpref, 0, 'NGC7814')
    # Chi squared
    chisquared = np.sum(residuals**2/comp.galdict('NGC7814')['m_v_errors']**2)
    dof = len(comp.galdict('NGC5533')['m_radii']) - 5       # number of degrees of freedom = number of observed data - number of fitting parameters
    reducedchisquared = chisquared / dof  
    
    props = dict(boxstyle='round', facecolor='white', alpha=0.5)
    ax4.text(19,390,r"Reduced $\chi^2$: {:.2f}".format(reducedchisquared),ha='right',va='top',bbox=props,size=22)
    
################################
######## Define Sliders ########
################################

### NGC 5533 ###
# Number of projected black dots slider
arraysize_5533 = FloatSlider(min=minnumberBH(5533), max=maxnumberBH(5533), step=stepN, 
                value=defaultnumber(5533), 
                description='Number of millions of tiny black holes (increasing by {:.0f} million)'.format(stepN), 
                readout=True,
                readout_format='.2d', 
                orientation='horizontal', 
                style=style, layout=layout)
"""Slider for controlling the number of black holes for NGC5533.

:type: ipywidgets.widgets.widget_float.FloatSlider
"""

# Mass of each black hole
massMiniBH_5533 = FloatSlider(min=minmassBH, max=maxmassBH, step=minmassBH, 
                value=defaultmass,
                description='Mass of each tiny black hole (in solar masses, increasing by {:.1f})'.format(minmassBH), 
                readout=True,
                readout_format='.1f',
                orientation='horizontal', 
                style=style, layout=layout)
"""Slider for controlling the black hole mass for NGC5533.

:type: ipywidgets.widgets.widget_float.FloatSlider
"""

# Cutoff radius
rcut_5533 = FloatSlider(min=minrcutBH, max=maxrcutBH(5533), step=minrcutBH, 
                value=defaultrcutBH(5533),
                description='Cutoff radius (in kpc, increasing by {:.1f})'.format(minrcutBH), 
                readout=True,
                readout_format='.1f',
                orientation='horizontal', 
                style=style, layout=layout)
"""Slider for controlling the cutoff radius for black hole placement for NGC5533.

:type: ipywidgets.widgets.widget_float.FloatSlider
"""

### NGC 7814 ###
# Number of projected black dots slider
arraysize_7814 = FloatSlider(min=minnumberBH(7814), max=maxnumberBH(7814), step=stepN, 
                value=defaultnumber(7814), 
                description='Number of millions of tiny black holes (increasing by {:.0f} million)'.format(stepN), 
                readout=True,
                readout_format='.2d', 
                orientation='horizontal', 
                style=style, layout=layout)
"""Slider for controlling the number of black holes for NGC7814.

:type: ipywidgets.widgets.widget_float.FloatSlider
"""

# Mass of each black hole
massMiniBH_7814 = FloatSlider(min=minmassBH, max=maxmassBH, step=minmassBH, 
                value=0.5,
                description='Mass of each tiny black hole (in solar masses, increasing by {:.1f})'.format(minmassBH), 
                readout=True,
                readout_format='.1f',
                orientation='horizontal', 
                style=style, layout=layout)
"""Slider for controlling the black hole mass for NGC7814.

:type: ipywidgets.widgets.widget_float.FloatSlider
"""

# Cutoff radius
rcut_7814 = FloatSlider(min=minrcutBH, max=maxrcutBH(7814), step=minrcutBH, 
                value=defaultrcutBH(7814),
                description='Cutoff radius (in kpc, increasing by {:.1f})'.format(minrcutBH), 
                readout=True,
                readout_format='.1f',
                orientation='horizontal', 
                style=style, layout=layout)
"""Slider for controlling the cutoff radius for black hole placement for NGC7814.

:type: ipywidgets.widgets.widget_float.FloatSlider
"""

def interactive_plot_5533(widgetfunction):
    """
    Generate an interactive plot widget, allowing the user to interact with the NGC5533 data and the galaxy's components.

    :parameters:
        widgetfunction: [function]
            A function that generates the base plot for the widget to alter. This should, in all likelihood, be :func:`f5533 <widget_BH.f5533>`.

    :returns: 
        [ipywidgets.widgets.interaction.interactive] -- creates sliders to make the plot interactive.

    .. seealso:: For an example usage of this function, see the notebook `10_Bonus_Black_Holes_as_DM.ipynb on Binder <https://mybinder.org/v2/gh/villano-lab/galactic-spin-W1/HEAD?labpath=binder%2F09_Widget_SPARC_Galaxies.ipynb>`__.

    """
    interact = interactive(widgetfunction, arraysize=arraysize_5533, 
                           scale=scale, massMiniBH=massMiniBH_5533, 
                           rcut=rcut_5533, continuous_update=False)
    return interact

def interactive_plot_7814(widgetfunction):
    """
    Generate an interactive plot widget, allowing the user to interact with the NGC7814 data and the galaxy's components.

    :parameters:
        widgetfunction: [function]
            A function that generates the base plot for the widget to alter. This should, in all likelihood, be :func:`f7814 <widget_BH.f7814>`.

    :returns: 
        [ipywidgets.widgets.interaction.interactive] -- creates sliders to make the plot interactive.

    .. seealso:: For an example usage of this function, see the notebook `10_Bonus_Black_Holes_as_DM.ipynb on Binder <https://mybinder.org/v2/gh/villano-lab/galactic-spin-W1/HEAD?labpath=binder%2F09_Widget_SPARC_Galaxies.ipynb>`__.

    """
    interact = interactive(widgetfunction, arraysize=arraysize_7814, 
                           scale=scale, massMiniBH=massMiniBH_7814, 
                           rcut=rcut_7814, continuous_update=False)
    return interact

################################
########### Button #############
################################

### NGC 5533 ###
# Button to revert back to Best Fit
button_5533 = Button(
    description="Best Fit",
    button_style='warning', # 'success', 'info', 'warning', 'danger' or ''
    icon='check')
"""A button that returns all settings for NGC5533 to the best fit.

:type: ipywidgets.widgets.widget_button.Button
"""
out_5533 = Output()
"""A handler for widget output NGC5533.

:type: ipywidgets.widgets.widget_output.Output
"""

def on_button_clicked_5533(_):
    """
    A function to reset values when the 'Best Fit' button for NGC5533 is clicked. 
    
    :parameters: None.

    :returns:
        None

    :example:
        >>> button_5533.on_click(on_button_clicked_5533)

        This renders the button click behavior seen in `10_Bonus_Black_Holes_as_DM.ipynb on Binder <https://mybinder.org/v2/gh/villano-lab/galactic-spin-W1/HEAD?labpath=binder%2F09_Widget_SPARC_Galaxies.ipynb>`__.
    """
    arraysize_5533.value = defaultnumber(5533)
    massMiniBH_5533.value = defaultmass
    rcut_5533.value = defaultrcutBH(5533)
button_5533.on_click(on_button_clicked_5533)

### NGC 7814 ###
# Button to revert back to Best Fit
button_7814 = Button(
    description="Best Fit",
    button_style='warning', # 'success', 'info', 'warning', 'danger' or ''
    icon='check')
"""A button that returns all settings for NGC7814 to the best fit.

:type: ipywidgets.widgets.widget_button.Button
"""
out_7814 = Output()
"""A handler for widget output for NGC7814.

:type: ipywidgets.widgets.widget_output.Output
"""

def on_button_clicked_7814(_):
    """
    A function to reset values when the 'Best Fit' button for NGC7814 is clicked. 
    
    :parameters: None.

    :returns:
        None

    :example:
        >>> button_7814.on_click(on_button_clicked_7814)

        This renders the button click behavior seen in `10_Bonus_Black_Holes_as_DM.ipynb on Binder <https://mybinder.org/v2/gh/villano-lab/galactic-spin-W1/HEAD?labpath=binder%2F09_Widget_SPARC_Galaxies.ipynb>`__.
    """
    arraysize_7814.value = defaultnumber(7814)
    massMiniBH_7814.value = 0.5
    rcut_7814.value = defaultrcutBH(7814)
button_7814.on_click(on_button_clicked_7814)