import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import numpy as np
from lidargo import utilities
import warnings
from lidargo.utilities import with_logging

# Suppress all graphical UserWarnings
warnings.filterwarnings(
    "ignore",
    message=".*interpreted as cell centers, but are not monotonically increasing or decreasing.*",
)

warnings.filterwarnings(
    "ignore",
    message=".*can be slow with large amounts of data.*",
)

def qcReport(ds, dsInput, qc_rws_range):
    """wrapper method to make qc figures"""
    wsqc_fig = windSpeedQCfig(ds, qc_rws_range)
    scanqc_fig = scanFig(ds)
    angscat_fig, _ = angScatter(dsInput, ds)
    anghist_fig = angHistFig(ds, dsInput)
    
    return wsqc_fig, scanqc_fig, angscat_fig, anghist_fig

@with_logging
def windSpeedQCfig(ds, qc_rws_range):
    """wrapper method to make qc and probability scatter plots"""
    fig = plt.figure(figsize=(10, 4), layout="constrained")
    gs = GridSpec(nrows=1, ncols=3, width_ratios=[6, 0.25, 6], figure=fig)

    ax0 = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])
    ax1 = fig.add_subplot(gs[0, 2])

    probabilityScatter(ds, ax=ax0, fig=fig, cax=cax)
    probabilityVSrws(ds, qc_rws_range, ax=ax1, fig=fig)

    fig.suptitle(
        titleGenerator(ds, "QC of data", components=["location", "date", "file"])
    )

    return fig

@with_logging
def scanFig(ds):
    """wrapper method to make scans pcolor figures"""
    fig = plt.figure(figsize=(18, 8))
   
    
    if ds.attrs['scan_mode'].lower()=='3d':
        projection='3d'
    else:
        projection='rectilinear'

    if ds.attrs['scan_mode'].lower()!='stare':
        gs = GridSpec(nrows=2, ncols=6, width_ratios=[6, 6, 6, 6, 6, 0.5], figure=fig)
        ax1 = fig.add_subplot(gs[0, 0],projection=projection)
        ax2 = fig.add_subplot(gs[1, 0],projection=projection)
        axt = [ax1] + [fig.add_subplot(gs[0, x], projection=projection) for x in range(1, 5)]
        axb = [ax2] + [fig.add_subplot(gs[1, x], projection=projection) for x in range(1, 5)]
        caxt = fig.add_subplot(gs[0, -1])
        caxb = fig.add_subplot(gs[1, -1])
    else:
        gs = GridSpec(nrows=2, ncols=2, width_ratios=[30, 0.5], figure=fig)
        axt = fig.add_subplot(gs[0, 0],projection=projection)
        axb = fig.add_subplot(gs[1, 0],projection=projection)
        caxt = fig.add_subplot(gs[0, -1])
        caxb = fig.add_subplot(gs[1, -1])

    fig, axt, _ = rws(ds, fig=fig, ax=axt, cax=caxt, cbar_label="Radial wind \n"+r"speed [m s$^{-1}$]")

    b1qc = ds.copy()
    b1qc["wind_speed"] = b1qc["wind_speed"].where(b1qc.qc_wind_speed == 0.0)

    fig, axb, _ = rws(b1qc, fig=fig, ax=axb, cax=caxb, cbar_label="QC radial wind \n"+r"speed [m s$^{-1}$]")
    
    fig.suptitle(
        titleGenerator(ds, "QC of data", components=["location", "date", "file"])
    )
    return fig

@with_logging
def angHistFig(ds, dsInput):
    """wrapper method to make angle histograms"""
    
    if ds.attrs['scan_mode'].lower()=='ppi':
        fig, ax = plt.subplots(1,1, figsize=(10, 6))
        fig, _ = anghist_1D(dsInput,ds,'azimuth', ax=ax, fig=fig)
        # fig, _ = angdiffhist_1D(dsInput, ds, 'azimuth',ax=ax[1], fig=fig,color='k')
    elif  ds.attrs['scan_mode'].lower()=='rhi':
        fig, ax = plt.subplots(1,1, figsize=(10, 6))
        fig, _ = anghist_1D(dsInput,ds,'elevation', ax=ax, fig=fig)
        # fig, _ = angdiffhist_1D(dsInput, ds,'elevation', ax=ax[1], fig=fig,color='k')
    elif  ds.attrs['scan_mode'].lower()=='3d':
        fig, ax = plt.subplots(1,1, figsize=(10, 6))
        fig, _ = anghist_2D(dsInput,ds, ax=ax, fig=fig)
        # fig, _ = angdiffhist_1D(dsInput, ds,'azimuth', ax=ax[1], fig=fig,color='k')
        # fig, _ = angdiffhist_1D(dsInput, ds,'elevation', ax=ax[2], fig=fig,color='k')
    elif ds.attrs['scan_mode'].lower()=='stare':
        return
        
    fig.suptitle(
        titleGenerator(ds, "Geometry standardization", components=["location", "date", "file"])
    )
    return fig

def probabilityScatter(ds, ax=None, cax=None, fig=None, **kwargs):
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (9, 8)))

    prob_arange = np.arange(
        np.log10(ds.qc_wind_speed.attrs["min_probability_range"]) - 1,
        np.log10(ds.qc_wind_speed.attrs["max_probability_range"]) + 1,
    )

    sp = ax.scatter(
        ds.rws_norm,
        ds.snr_norm,
        s=3,
        c=np.log10(ds.probability),
        cmap=kwargs.get("cmap", "hot"),
        vmin=prob_arange[0],
        vmax=prob_arange[-1],
    )
    ax.set_xlabel(r"Normalized radial wind speed [m s$^{-1}$]")
    ax.set_ylabel("Normalized SNR [dB]")
    ax.grid(True)

    if cax is None:
        cax = fig.add_axes(
            [
                ax.get_position().x0 + ax.get_position().width + 0.01,
                ax.get_position().y0,
                0.015,
                ax.get_position().height,
            ]
        )
    cbar = plt.colorbar(sp, cax=cax, label="Probability")
    cbar.set_ticks(prob_arange)
    cbar.set_ticklabels([r"$10^{" + str(int(p)) + "}$" for p in prob_arange])
    # fig.tight_layout()
    return ax


# Second function: Semilog plot
def probabilityVSrws(ds, qc_rws_range, ax=None, fig=None, **kwargs):
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (9, 8)))

    ax.semilogx(
        ds.probability.values.ravel(),
        ds.rws_norm.values.ravel(),
        '.',
        color='C0',
        alpha=kwargs.get("alpha", 0.1),
    )
    ax.semilogx(
        0,
        0,
        '.',
        color='C0',
        label=kwargs.get("label_all", "All points"),
    )
    ax.semilogx(
        [10**b.mid for b in qc_rws_range.index],
        qc_rws_range.values,
        "-^",
        color='C1',
        markersize=kwargs.get("markersize", 5),
        label=kwargs.get("label_range", "Range"),
    )
    ax.semilogx(
        [
            ds["qc_wind_speed"].attrs["qc_probability_threshold"],
            ds["qc_wind_speed"].attrs["qc_probability_threshold"],
        ],
        [
            -ds["qc_wind_speed"].attrs["rws_norm_limit"],
            ds["qc_wind_speed"].attrs["rws_norm_limit"],
        ],
        "--",
        color='C2',
        label=kwargs.get("label_threshold", "Threshold"),
    )

    ax.set_xlabel("Probability")
    ax.set_ylabel(r"Normalized radial wind speed [m s$^{-1}$]")
    ax.yaxis.set_label_position("right")
    ax.legend()
    ax.grid(True)

    return ax

def rws(ds, ax=None, fig=None, cax=None, cbar_label="Radial wind \n"+r"speed [m s$^{-1}$]", **kwargs):
    """
    Plot radial wind speed (RWS) data in different projections based on scan type.

    Parameters:
    -----------
    ds : xarray.Dataset
        Dataset containing the RWS data.
    """

    if ds.attrs["scan_mode"].lower() == "ppi":
        fig, ax, cbar = ppi(ds, ax=ax, fig=fig, cax=cax, cbar_label=cbar_label)
    elif ds.attrs["scan_mode"].lower() == "rhi":
        fig, ax, cbar = rhi(ds, ax=ax, fig=fig, cax=cax ,cbar_label=cbar_label)
    elif ds.attrs["scan_mode"].lower() == "3d":
        fig, ax, cbar = volumetric(ds, ax=ax, fig=fig, cax=cax, cbar_label=cbar_label)
    elif ds.attrs["scan_mode"].lower() == "stare":
        fig, ax, cbar = stare(ds, ax=ax, fig=fig, cax=cax, cbar_label=cbar_label)
    else:
        raise ValueError(f"Unsupported scan type: {ds.attrs['scan_mode']}")

    return fig, ax, cbar


def ppi(ds, n_subplots: int = 5, ax=None, fig=None, cax=None, cbar_label="Radial wind \n"+r"speed [m s$^{-1}$]", **kwargs):
    """Plot plan position indicator (PPI) for radial wind speed data."""

    if fig is None or ax is None:
        fig, ax = plt.subplots(
            1,
            n_subplots,
            figsize=kwargs.get("figsize", (9, 8)),
        )

    scans = np.linspace(
        ds.scanID.values.min(), ds.scanID.values.max(), len(ax), dtype=int
    )

    for i, scan in enumerate(scans):
        subset = ds.isel(scanID=scan)
        im = ax[i].pcolormesh(
            subset.x, subset.y, subset.wind_speed, cmap="RdBu_r", shading="auto"
        )
        ax[i].set_xlabel(r"$x$ [m]")
        if i == 0:
            ax[i].set_ylabel(r"$y$ [m]")
        else:
            ax[i].set_yticklabels([])
        ax[i].set_aspect("equal")
        add_time_title(ax[i], ds.time.sel(scanID=scan))
        ax[i].grid(True)
        
    utilities.same_axis(ax)
    
    if cax is None:
        fig.tight_layout()
        cbar = add_colorbar(fig, ax[-1], im, cbar_label)
    else:
        cbar = plt.colorbar(im, cax=cax, label=cbar_label)
        new_pos=[cax.get_position().x0,
                          ax[-1].get_position().y0,
                          cax.get_position().width,
                          ax[-1].get_position().height]
        cax.set_position(new_pos) 

    return fig, ax, cbar

def rhi(ds, n_subplots: int = 5, cbar_label="Radial wind \n"+r"speed [m s$^{-1}$]",ax=None, fig=None, cax=None, **kwargs):
    """Plot range height indicator (RHI) for radial wind speed data."""
    
    if fig is None or ax is None:
        fig, ax = plt.subplots(
            1,
            n_subplots,
            figsize=kwargs.get("figsize", (9, 8)),
        )

    scans = np.linspace(
        ds.scanID.values.min(), ds.scanID.values.max(),  len(ax), dtype=int
    )

    for i, scan in enumerate(scans):
        subset = ds.isel(scanID=scan)
        im = ax[i].pcolormesh(
            subset.x, subset.z, subset.wind_speed, cmap="RdBu_r", shading="auto"
        )
        ax[i].set_xlabel(r"$x$ [m]")
        if i == 0:
            ax[i].set_ylabel(r"$z$ [m]")
        else:
            ax[i].set_yticklabels([])
        ax[i].set_aspect("equal")
        add_time_title(ax[i], ds.time.sel(scanID=scan))
        ax[i].grid(True)
        
    utilities.same_axis(ax)

    if cax is None:
        fig.tight_layout()
        cbar = add_colorbar(fig, ax[-1], im, cbar_label)
    else:
        
        cbar = plt.colorbar(im, cax=cax, label=cbar_label)
        new_pos=[cax.get_position().x0,
                          ax[-1].get_position().y0,
                          cax.get_position().width,
                          ax[-1].get_position().height]

        cax.set_position(new_pos) 

    return fig, ax, cbar

def volumetric(ds, n_subplots: int = 5, cbar_label="Radial wind \n"+r"speed [m s$^{-1}$]",ax=None, fig=None, cax=None, **kwargs):
    """Plot 3D visualization of radial wind speed data."""
    
    if fig is None or ax is None:
        fig, ax = plt.subplots(
            1,
            n_subplots,
            figsize=kwargs.get("figsize", (9, 8)),
        )

    scans = np.linspace(
        ds.scanID.values.min(), ds.scanID.values.max(), len(ax), dtype=int
    )
    
    for i, scan in enumerate(scans):
        subset = ds.isel(scanID=scan)
        sc=rws3Dscatter(ax[i], subset.x.values, subset.y.values, subset.z.values, subset.wind_speed.values)
        add_time_title(ax[i], subset.time)
            
        ax[i].set_xlabel(r"$x$ [m]")
        if i ==  len(ax)-1:
            ax[i].set_ylabel(r"$y$ [m]")
            ax[i].set_zlabel(r"$z$ [m]")
        else:
            ax[i].set_yticklabels([])
            ax[i].set_zticklabels([])
    
    utilities.same_axis(ax)
    
    if cax is None:
        fig.tight_layout()
        cbar = add_colorbar(fig, ax[-1], sc,label=cbar_label)
    else:
        
        cbar = plt.colorbar(sc, cax=cax,label=cbar_label)
        new_pos=[cax.get_position().x0+0.03,
                          ax[-1].get_position().y0,
                          cax.get_position().width,
                          ax[-1].get_position().height]
        
        cax.set_position(new_pos) 

    return fig, ax, cbar

def stare(ds,cbar_label="Radial wind \n"+r"speed [m s$^{-1}$]",ax=None, fig=None, cax=None, **kwargs):
    """Plot stare visualization for radial wind speed data."""
    
    if fig is None or ax is None:
        fig, ax = plt.subplots(
            1,
            1,
            figsize=kwargs.get("figsize", (9, 8)),
        )
    
    im = ax.pcolormesh(
        ds.time, ds.range, ds.wind_speed.squeeze(), cmap="RdBu_r", shading="auto"
    )
    ax.set_xlabel(r"Time (UTC)")
    ax.set_ylabel(r"Range [m]")
    ax.grid(True)
    
    xformatter = mdates.DateFormatter("%H:%M")
    ax.xaxis.set_major_formatter(xformatter)

    if cax is None:
        fig.tight_layout()
        cbar = add_colorbar(fig, ax, im, cbar_label)
    else:
        cbar = plt.colorbar(im, cax=cax, label=cbar_label)
        
    return fig, ax, cbar

@with_logging
def angScatter(dsInput, dsStandardized, ax=None, fig=None, **kwargs):
    """Scatter plot showing observed and standardized azimuth and elevation angles"""
    if fig is None or ax is None:
        fig, ax = plt.subplots(2,1,figsize=kwargs.get("figsize", (16, 8)))

    #azimuth time series
    ax[0].scatter(
        dsInput.time,
        dsInput.azimuth,
        marker=".",
        c="C0",
        label="Input data",
    )
    ax[0].scatter(
        dsStandardized.time,
        dsStandardized.azimuth,
        marker=".",
        edgecolor="C1",
        facecolor='none',
        label="Standardized data",
    )
 
    xformatter = mdates.DateFormatter("%H:%M")
    ax[0].xaxis.set_major_formatter(xformatter)
    ax[0].set_xlabel("Time (UTC)")
    ax[0].set_ylabel("Azimuth angle [˚]")
 
    ax[0].set_title(
        titleGenerator(
            dsStandardized,
            "Azimuth angles",
            ["location", "date", "file"],
        )
    )
    ax[0].legend()
    ax[0].grid(True)
    
    #elevation time series
    ax[1].scatter(
        dsInput.time,
        dsInput.elevation,
        marker=".",
        c="C0",
        label="Input data",
    )
    ax[1].scatter(
        dsStandardized.time,
        dsStandardized.elevation,
        marker=".",
        edgecolor="C1",
        facecolor='none',
        label="Standardized data",
    )

    xformatter = mdates.DateFormatter("%H:%M")
    ax[1].xaxis.set_major_formatter(xformatter)
    ax[1].set_xlabel("Time (UTC)")
    ax[1].set_ylabel("Elevation angle [˚]")

    ax[1].set_title(
        titleGenerator(
            dsStandardized,
            "Elevation angles",
            ["location", "date", "file"],
        )
    )
    ax[1].legend()
    ax[1].grid(True)
    
    fig.tight_layout()
    
    return fig, ax

def anghist_1D(dsInput,ds,which_angle='azimuth',ax=None, fig=None, **kwargs):
    """Bar plot of occurrences of angles"""
    
    assert which_angle in ['azimuth','elevation'], f'{which_angle} is not a valid beam angle'
        
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (5, 3)))
    
    
    ang=dsInput[which_angle].values.flatten()
    counts, bins = np.histogram(ang, bins=utilities.rev_mid(np.unique(ang)))
    ax.bar(np.unique(ang),counts, width=0.5,color='C0',alpha=0.75,label='Input data', **kwargs)

    ang=ds[which_angle].values.flatten()
    counts, bins = np.histogram(ang, bins=utilities.rev_mid(np.unique(ang)))
    ax.bar(np.unique(ang),counts, width=0.5,alpha=1,edgecolor='C1',facecolor='none',label='Standardized data', **kwargs)
    ax.set_xlabel(f"{which_angle.capitalize()} angle [˚]")
    ax.set_ylabel("Occurrence")
    ax.legend()
    ax.grid(True)

    return fig, ax

def anghist_2D(dsInput,ds,which_angle='azimuth',ax=None, fig=None, **kwargs):
    """2D trajectory of scans colored by occurrence"""
        
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (5, 3)))
    
    azi=dsInput['azimuth'].values.flatten()
    ele=dsInput['elevation'].values.flatten()
    ax.plot(azi,ele,'.',color='C0',markersize=12,alpha=0.5,label='Input data', **kwargs)
    
    azi=ds['azimuth'].mean(dim='scanID').values.flatten()
    ele=ds['elevation'].mean(dim='scanID').values.flatten()
    
    ax.plot(azi,ele,'--.',color='C1',markersize=10,label='Standardized data', **kwargs)
    ax.set_xlabel(r'Azimuth [$^\circ$]')
    ax.set_ylabel(r'Elevation [$^\circ$]')
    ax.legend()
    ax.grid(True)

    return fig, ax

def rws3Dscatter(ax, x, y, z, f,n_max=10000):
    """Helper function for 3D scatter plotting."""
    
    #exclude nans
    real = ~np.isnan(x+y+z+f)
    
    #subsample if too many points
    skip = int(np.sum(real) / n_max) if np.sum(real) > n_max else 1
    
    #plot
    sc = ax.scatter(
        x[real][::skip],
        y[real][::skip],
        z[real][::skip],
        s=2,
        c=f[real][::skip],
        cmap="coolwarm",
        vmin=np.nanpercentile(f, 5) - 1,
        vmax=np.nanpercentile(f, 95) + 1,
    )

    xlim = [np.min(x), np.max(x)]
    ylim = [np.min(y), np.max(y)]
    zlim = [np.min(z), np.max(z)]
    
    ax.set_box_aspect((np.diff(xlim)[0], np.diff(ylim)[0], np.diff(zlim)[0]))
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_zlim(zlim)
    
    return sc

def add_colorbar(fig, ax, mappable, label, position_adjust=0.01):
    """Helper function to add colorbar."""
    cax = fig.add_axes(
        [
            ax.get_position().x0 + ax.get_position().width + position_adjust,
            ax.get_position().y0,
            0.015,
            ax.get_position().height,
        ]
    )
    return plt.colorbar(mappable, cax=cax, label=label)

def titleGenerator(ds, inputString: str = None, components=["location", "date"]):
    """Build title for figures"""
    componentDict = {
        "date": f"on {ds.time.dt.strftime('%Y-%m-%d').values.flatten()[0]}",
        "location": f"at {ds.attrs['location_id']}",
        "file": f"\nFile: {ds.attrs['datastream']}",
    }

    title = [inputString] + [componentDict[comp] for comp in components]

    return " ".join(title)

def add_time_title(ax, time):
    """Helper function to add time-only title."""
    ax.set_title(
        f"{utilities.nanmin_time(time,'%H:%M:%S')} - "
        f"{utilities.nanmax_time(time,'%H:%M:%S')}"
    )