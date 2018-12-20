#! /usr/bin/env python

"""
Tools for generating Mirage-compatible catalogs from surveys

Note that once you have mirage-formatted catalogs, there is an "add_catalog" function
in catalog_generator.py that can combine catalogs

"""

from astropy.coordinates import SkyCoord
import os
import math
import astropy.units as u
from astroquery.gaia import Gaia
from astroquery.irsa import Irsa
from astropy.table import Table
import numpy as np
from collections import OrderedDict
#import distortion

from mirage.catalogs.catalog_generator import PointSourceCatalog, GalaxyCatalog


def for_proposal(pointing_dictionary, catalog_splitting_threshold=1., instrument, filter_list, email=''):
    """
    NOT YET FUNCTIONAL

    Given a pointing dictionary from an APT file, generate source catalogs
    that cover all of the coordinates specifired.

    Parameters
    ----------
    pointing_dictionary : dict
        Output from miarge.apt.apt_inputs.ra_dec_update()

    catalog_splitting_threshold : float
        Maximum distance in degrees between two pointings where a single catalog will contain
        both pointings

    Returns
    -------
    something
    """
    threshold = catalog_splitting_threshold * u.deg
    ra_apertures = pointing_dictionary['ra_ref'] * u.deg
    dec_apertures = pointing_dictionary['dec_ref'] * u.deg
    ra_target = pointing_dictionary['ra'] * u.deg
    dec_target = pointing_dictionary['dec'] * u.deg
    mapped = np.array([False] * len(ra_target))
    index = np.arange(len(ra_target))

    for indx, target_ra, target_dec in zip(index, ra_target, dec_target):
        if mapped[indx] is False:
            dithers = ra_target == target_ra & dec_target == target_dec
            min_ra = np.min(ra_apertures[dithers])
            max_ra = np.max(ra_apertures[dithers])
            min_dec = np.min(dec_apertures[dithers])
            max_dec = np.max(dec_apertures[dithers])

#            nearby_targets = separation(target_ra, target_dec to ra_target, dec_target) < catalog_splitting_threshold &
#                            mapped is False
            for close_target in nearby_targets:
                dithers = ra_target == ra_target[close_target] & dec_target == dec_target[close_target]
                min_ra = np.min([ra_apertures[dithers]].append(min_ra))
                max_ra = np.max([ra_apertures[dithers]].append(max_ra))
                min_dec = np.min([dec_apertures[dithers]].append(min_dec))
                max_dec = np.max([dec_apertures[dithers]].append(max_dec))
            mapped[nearby_targets] = True

            # Pad min and max RA and Dec values since so far we have values only at the reference
            # location. Add at least half a (LW) detector width * sqrt(2).
            pad = 0.062 * 1024 * 1.5
            min_ra -= pad
            max_ra += pad
            min_dec -= pad
            max_dec += pad
            mean_ra = (max_ra + min_ra) / 2.
            mean_dec = (max_dec + min_dec) / 2.
            delta_ra = max_ra - min_ra
            delta_dec = max_dec - min_dec
            full_width = np.max([delta_ra, delta_dec])

            # Create catalog(s)
            if point_source:
                ptsrc_cat = get_all_catalogs(mean_ra, mean_dec, full_width, instrument=instrument, filters=filter_list,
                                             email=email)
            else:
                ptsrc_cat = None

            if extragalactic:
                galaxy_cat = galaxy_background(mean_ra, mean_dec, 0., full_width, instrument, filter_list,
                                               boxflag=False, brightlimit=14.0, seed=None)
            else:
                galaxy_cat = None

            Now_save_the_catalogs_and_return_filenames
#            cat_filename = '???????'
#            cat_dir = '???????'
#            cat.save(os.path.join(cat_dir, cat_filename))


def query_2MASS_ptsrc_catalog(ra, dec, box_width):
    """
    Query the 2MASS All-Sky Point Source Catalog in a square region around the RA and Dec
    provided. Box width must be in units of arcseconds

    Parameters
    ----------
    ra : float or str
        Right ascention of the center of the catalog. Can be decimal degrees or HMS string

    dec : float or str
        Declination of the center of the catalog. Can be decimal degrees of DMS string

    box_width : float
        Width of the box in arcseconds containing the catalog.

    Returns
    -------

    query_table : astropy.table.Table
        Catalog composed of MaskedColumns containing 2MASS sources

    magnitude_column_names : list
        List of column header names corresponding to columns containing source magnitude
    """
    # Don't artificially limit how many sources are returned
    Irsa.ROW_LIMIT = -1

    ra_dec_string = "{}  {}".format(ra, dec)
    query_table = Irsa.query_region(ra_dec_string, catalog='fp_psc', spatial='Box',
                                    width=box_width * u.arcsec)

    # Exclude any entries with missing RA or Dec values
    radec_mask = filter_bad_ra_dec(query_table)
    query_table = query_table[radec_mask]

    # Column names of interest
    magnitude_column_names = ['j_m', 'h_m', 'k_m']
    #cat = PointSourceCatalog(ra=query_table['ra'].data.data.data[radec_mask],
    #                         dec=query_table['dec'].data.data.data[radec_mask])
    #
    # Add the J, H, and K magnitudes as they may be useful for magnitude conversions later
    # Add the values that have had fill_values applied. The fill_value is 1e20.
    #for key in ['j_m', 'h_m', 'k_m']:
    #    data = query_table[key].filled().data
    #    cat.add_magnitude_column(data, instrument='2MASS', filter_name=key)

    return query_table, magnitude_column_names


def query_WISE_ptsrc_catalog(ra, dec, box_width):
    """Query the WISE All-Sky Point Source Catalog in a square region around the RA and Dec
    provided. Box width must be in units of arcseconds

    Parameters
    ----------
    ra : float or str
        Right ascention of the center of the catalog. Can be decimal degrees or HMS string

    dec : float or str
        Declination of the center of the catalog. Can be decimal degrees of DMS string

    box_width : float
        Width of the box in arcseconds containing the catalog.

    Returns
    -------

    query_table : astropy.table.Table
        Catalog composed of MaskedColumns containing WISE sources

    magnitude_column_names : list
        List of column header names corresponding to columns containing source magnitude
    """
    # Don't artificially limit how many sources are returned
    Irsa.ROW_LIMIT = -1

    ra_dec_string = "{}  {}".format(ra, dec)
    query_table = Irsa.query_region(ra_dec_string, catalog='allsky_4band_p3as_psd', spatial='Box',
                                    width=box_width * u.arcsec)

    # Exclude any entries with missing RA or Dec values
    radec_mask = filter_bad_ra_dec(query_table)
    query_table = query_table[radec_mask]

    # Column names of interest
    magnitude_column_names = ['w1mpro', 'w2mpro', 'w3mpro', 'w4mpro']
    return query_table, magnitude_column_names


def mirage_ptsrc_catalog_from_table(table, instrument, mag_colnames, magnitude_system='vegamag'):
    """Create a mirage-formatted point source catalog from an input
    table (e.g. from one of the query functions), along with the magnitude
    column names of interest

    Parameters
    ----------

    table : astropy.table.Table
        Source catalog from (e.g.) Gaia or 2MASS query

    instrument : str
        Unique identifier for where data came from (e.g. '2MASS', 'WISE', 'nircam_f200w')

    mag_colnames : list
        List of strings corresponding to the columns in 'table' that contain magnitude values

    magnitude_system : str
        This is the label for the magnitude system, 'vegamag', 'abmag', or 'stmag'.
    """
    cat = PointSourceCatalog(ra=table['ra'].data.data, dec=table['dec'].data.data)

    for magcol in mag_colnames:
        data = table[magcol].filled().data
        cat.add_magnitude_column(data, instrument=instrument, filter_name=magcol,
                                 magnitude_system=magnitude_system)
    return cat


def get_2MASS_ptsrc_catalog(ra, dec, box_width):
    """Wrapper around 2MASS query and creation of mirage-formatted catalog"""
    twomass_cat, twomass_mag_cols = query_2MASS_ptsrc_catalog(ra, dec, box_width)
    twomass_mirage = mirage_ptsrc_catalog_from_table(twomass_cat, '2MASS', twomass_mag_cols)
    return twomass_mirage, twomass_cat


def twoMASS_plus_background(ra, dec, box_width, kmag_limits=(17, 29), email=''):
    """Convenience function to create a catalog from 2MASS and add a population of
    fainter stars. In this case, cut down the magnitude limits for the call to the
    Besancon model so that we don't end up with a double population of bright stars
    """
    two_mass, twomass_cat = get_2MASS_ptsrc_catalog(ra, dec, box_width)
    background, background_cat = besancon(ra, dec, box_width, coords='ra_dec', email=email)
    two_mass.add_catalog(background)
    return two_mass


def get_all_catalogs(ra, dec, box_width, kmag_limits=(10, 29), email='', instrument='NIRISS', filters=[]):
    """
    This is a driver function to query the GAIA/2MASS/WISE catalogues
    plus the Besancon model and combine these into a single JWST source list.
    The routine cuts off the bright end of the Besancon model to match the input
    2MASS catalogue, so as to avoid getting too many bright stars in the
    output catalogue.

    For the observed values, the code interpolates the photon-weighted mean
    flux density values in wavelength to get the NIRCam/NIRISS/Guider magnitudes.
    This process is nominally OK when there is extinction, but only when the
    spectrum is relatively smooth (so it is suspect for stars with very deep
    moelcular bands over the near-infrared wavelengths).

    For the Bescancon values, the VJHKL magnitudes are matched to Kurucz models
    and then the extinction is applied.  This process is limited by the range
    of Kurucz models considered., and to some degree by the simple extinction
    model used in the Besancon code.

    Input values:

        ra:           (float or str)
                      right ascension of the target field in degrees or HMS
        dec:          (float or str)
                      declination of the target field in degrees or DMS
        box_width:    (float)
                      size of the (square) target field in arc-seconds
        kmag_limits:  (tuple)
                      optional limits on the K magnitudes for the Besancon model
        email:        (string)
                      email address required for the Besancon model server
        instrument:   (string)
                      One of "all", "NIRISS", "NIRCam", or "Guider"
        filters:      (list of strings)
                      Either an empty list (which gives all filters) or a list
                      of filter names (i.e. F090W) to be calculated.

    Return values:

        source_list:   (astropy.table.Table)
                       A table with the filter magnitudes
        filter_names:  (list)
                       A list of the filter name header strings for writing to
                       an output file.
    """
    if isinstance(ra, str):
        pos = SkyCoord(ra, dec, frame='icrs')
        outra = pos.ra.deg
        outdec = pos.dec.deg
    else:
        outra = ra
        outdec = dec
    filter_names = make_filter_names(instrument, filters)
    gaia_cat, gaia_mag_cols, gaia_2mass, gaia_2mass_crossref, gaia_wise, \
        gaia_wise_crossref = query_GAIA_ptsrc_catalog(outra, outdec, box_width)
    twomass_cat, twomass_cols = query_2MASS_ptsrc_catalog(outra, outdec, box_width)
    wise_cat, wise_cols = query_WISE_ptsrc_catalog(outra, outdec, box_width)
    besancon_cat, besancon_model = besancon(outra, outdec, box_width,
                                            email=email, kmag_limits=kmag_limits)
    besancon_jwst = transform_besancon(besancon_cat, besancon_model, instrument, filter_names)
    if len(filter_names) != len(filters):
        newfilters = []
        for loop in range(len(filter_names)):
            values = filter_names[loop].split('_')
            newfilters.append(values[1])
    else:
        newfilters = filters
    for loop in range(len(filters)):
        besancon_cat.add_magnitude_column(np.squeeze(besancon_jwst[:, loop]), instrument=instrument,
                                          filter_name=newfilters[loop], magnitude_system='vegamag')
    observed_jwst = combine_and_interpolate(gaia_cat, gaia_2mass, gaia_2mass_crossref, gaia_wise,
                                            gaia_wise_crossref, twomass_cat, wise_cat, instrument, filters)
    print('Adding %d sources from Besancon to %d sources from the catalogues.' % (len(besancon_cat.ra),
                                                                                  len(observed_jwst.ra)))
    source_list = combine_catalogs(observed_jwst, besancon_cat)
    return source_list, filter_names


def transform_besancon(besancon_cat, besancon_model, instrument, filter_names):
    """
    Given the output from a Besancon model, transform to JWST magnitudes by
    making a best match to the standard BOSZ model colours for the VJHKL
    magnitudes, then taking the BOSZ results for the JWST filters.  Apply
    any ISM extinction after the matching.

    One possible improvement would be to interpolate between the best matches
    rather than just taking the best one.

    Input values:

    besancon_cat:  (mirage.catalogs.create_catalog.PointSourceCatalog object)
                   This has the RA/Dec/VJHKL magnitude values for the sources

    besancon_model:  (astropy.table.Table object)
                     This has the Besancon model results in a Table.  The
                     ISM extinction value is needed here.

    filter_names:    (list of strings)
                     The list of the requried output NIRCam/NIRISS/Guider
                     filter magnitudes.

    Return values:

    out_magnitudes:  (numpy array)
                     A two-dimensional float numpy array with the star number
                     in the first dimension and the estimated JWST magnitudes
                     in the second dimension.

                     A value of None is returned if the matching fails.  This
                     should not happen with the regular inputs.
    """
    standard_magnitudes, standard_values, standard_filters, standard_labels = read_standard_magnitudes()
    nstars = len(besancon_cat.ra)
    nfilters = len(filter_names)
    out_magnitudes = np.zeros((nstars, nfilters), dtype=np.float32)
    inds = crossmatch_filter_names(filter_names, standard_filters)
    in_magnitudes = np.zeros((4), dtype=np.float32)
    vmags = besancon_model['V'].data
    kmags = (besancon_model['V'] - besancon_model['V-K']).data
    jmags = kmags + besancon_model['J-K'].data
    hmags = jmags - besancon_model['J-H'].data
    lmags = jmags - besancon_model['J-L'].data
    in_filters = ['Johnson V', 'Johnson J', 'Johnson H', 'Johnson K']
    for loop in range(nstars):
        in_magnitudes[0] = vmags[loop]
        in_magnitudes[1] = jmags[loop]
        in_magnitudes[2] = hmags[loop]
        in_magnitudes[3] = kmags[loop]
        newmags = match_model_magnitudes(in_magnitudes, in_filters, standard_magnitudes, standard_values,
                                         standard_filters, standard_labels)
        if newmags is None:
            return None
        newmags = besancon_model['Av'][loop]*standard_values[3, :]+newmags
        out_magnitudes[loop, :] = newmags[inds]
    return out_magnitudes


def crossmatch_filter_names(filter_names, standard_filters):
    inds = []
    for loop in range(len(filter_names)):
        for n1 in range(len(standard_filters)):
            if filter_names[loop] in standard_filters[n1]:
                inds.append(n1)
    return inds


def match_model_magnitudes(in_magnitudes, in_filters, standard_magnitudes,
                           standard_values, standard_filters, standard_labels):
    """
    This code attempts to make the best match between a set of input magnitudes
    and a set of BOSZ simulated magnitudes.  It is assumed that the input
    magnitudes are not reddened.  The match is for the smallest root-mean-square
    deviation between the input magnitudes and the BOSZ model magnitudes, with
    an overall offset factor applied to the latter.

    Input Values:

    in_magnitudes:   (numpy vector of floats)
                     The list of (A0V) magnitude values to match.

    in_filters:      (list of str)
                     The labels for the magnitudes.

    standard_magntudes:   (numpy two-dimensional array of floats)
                          The standard simulated magnitude values.

    standard_values:      (numpy two-dimensional array of floats)
                          An array of other filter values (wavelengths,
                          zero magnitude flux density values, extinction)

    standard_filters:     (list of strings)
                          The list of the standard magnitude filter names

    standard_labels:      (list of strings)
                          The labels for the input stellar atmosphere models
                          used to calculate the standard magnitudes.

    Return values:

    out_magnitudes:       (numpy vector of floats) or None
                          The full set of estimated magnitudes from the model
                          matching, or None if a problem occurs.
    """
    inds = crossmatch_filter_names(in_filters, standard_filters)
    nmatch = float(len(inds))
    if nmatch != len(in_filters):
        print('Error in matching the requested filters for model matching.')
        return None
    subset = np.copy(standard_magnitudes[:, inds])
    dim1 = subset.shape
    nmodels = dim1[0]
    rmsmin = 1.e+20
    nmin = 0
    omin = 0.
    for loop in range(nmodels):
        del1 = subset[loop, :] - in_magnitudes
        offset = np.mean(del1)
        delm = (subset[loop, :] - offset - in_magnitudes)
        rms = math.sqrt(np.sum(delm*delm)/nmatch)
        if rms < rmsmin:
            rmsmin = rms
            nmin = loop
            omin = offset
    out_magnitudes = np.copy(standard_magnitudes[nmin, :]-omin)
    return out_magnitudes


def read_standard_magnitudes():
    """
    Input values:

    None

    Return values:

    standard_magntudes:   (numpy two-dimensional array of floats)
                          The standard simulated magnitude values.

    standard_values:      (numpy two-dimensional array of floats)
                          An array of other filter values (wavelengths,
                          zero magnitude flux density values, extinction)

    standard_filters:     (list of strings)
                          The list of the standard magnitude filter names

    standard_labels:      (list of strings)
                          The labels for the input stellar atmosphere models
                          used to calculate the standard magnitudes.

    The code reads a file magslist_bosz_normal_mirage1.new to get the simulated
    magnitudes.  This file gives simulated magnitudes for the Johnson VJHKL
    filters, the 2MASS filters, the WISE filters, the GAIA filters, and the
    JWST filters.  Also some filter specific values are read from the header
    lines of the file.
    """
    # read in the values needed to transform the Besancon model magnitudes
    #
    path = os.environ.get('MIRAGE_DATA')
    standard_mag_file = os.path.join(path, 'niriss/catalogs/', 'magslist_bosz_normal_mirage.new')
    with open(standard_mag_file, 'r') as infile:
        lines = infile.readlines()

    standard_magnitudes = np.loadtxt(standard_mag_file, comments='#')
    # standard_values holds the wavelengths (microns), zero magnitude flux
    # density values (W/m^2/micron and Jy) and the relative ISM extinction
    standard_values = np.zeros((4, 58), dtype=np.float32)
    # The following list is manually produced, but must match the order
    # of filters in the input file, where the names are a bit different.
    # Note that for the GAIA g filter the trailing space is needed to
    # allow the code to differentiate the G, BP, and RP filters.
    standard_filters = ['Johnson V', 'Johnson H', 'Johnson H', 'Johnson K',
                        '2MASS J', '2MASS H', '2MASS Ks', 'Johnson L',
                        'WISE W1', 'WISE W2', 'WISE W3', 'WISE W4', 'GAIA g ',
                        'GAIA gbp', 'GAIA grp',
                        'niriss_f090w_magnitude', 'niriss_f115w_magnitude',
                        'niriss_f140w_magnitude', 'niriss_f150w_magnitude',
                        'niriss_f158w_magnitude', 'niriss_f200w_magnitude',
                        'niriss_f277w_magnitude', 'niriss_f356w_magnitude',
                        'niriss_f380w_magnitude', 'niriss_f430w_magnitude',
                        'niriss_f444w_magnitude', 'niriss_f480w_magnitude',
                        'guider1_magnitude', 'guider2_magnitude',
                        'nircam_f070w_magnitude', 'nircam_f090w_magnitude',
                        'nircam_f115w_magnitude', 'nircam_f140w_magnitude',
                        'nircam_f150w_magnitude', 'nircam_f150w2_magnitude',
                        'nircam_f162w_magnitude', 'nircam_f164w_magnitude',
                        'nircam_f182w_magnitude', 'nircam_f187w_magnitude',
                        'nircam_f200w_magnitude', 'nircam_f210w_magnitude',
                        'nircam_f212w_magnitude', 'nircam_f250w_magnitude',
                        'nircam_f277w_magnitude', 'nircam_f300w_magnitude',
                        'nircam_f322w2_magnitude', 'nircam_f323w_magnitude',
                        'nircam_f335w_magnitude', 'nircam_f356w_magnitude',
                        'nircam_f360w_magnitude', 'nircam_f405w_magnitude',
                        'nircam_f410w_magnitude', 'nircam_f430w_magnitude',
                        'nircam_f444w_magnitude', 'nircam_f460w_magnitude',
                        'nircam_f466w_magnitude', 'nircam_f470w_magnitude',
                        'nircam_f480w_magnitude']
    standard_labels = []
    n1 = 0
    for line in lines:
        line = line.strip('\n')
        if '#' in line[0:1]:
            values = line.split('#')
            if len(values) == 3:
                v1 = values[-1].split()
                for loop in range(4):
                    standard_values[loop, n1] = float(v1[loop])
                n1 = n1 + 1
        else:
            values = line.split('#')
            standard_labels.append(values[-1])
    return standard_magnitudes, standard_values, standard_filters, standard_labels


def combine_and_interpolate(gaia_cat, gaia_2mass, gaia_2mass_crossref, gaia_wise,
                            gaia_wise_crossref, twomass_cat, wise_cat, instrument, filter_names):
    """
    The routine combines GAIA/2MASS/WISE photometry to estimate JWST filter
    magnitudes.  The algorithm depends a bit on what magnitudes are available.

    Input values:

    gaia_cat:     (astropy.table.Table)
                  contains GAIA DR2 search results in table form

    gaia_2mass:   (astropy.table.Table)
                  contains 2MASS catalogue values from the GAIA DR2 archive

    gaia_2mass_crossref:   (astropy.table.Table)
                           contain GAIA/2MASS cross-references from the GAIA DR2 archive

    gaia_wise:    (astropy.table.Table)
                  contains WISE catalogue values from the GAIA DR2 archive

    gaia_wise_crossref:    (astropy.table.Table)
                           contains GAIA/WISE cross-references from the GAIA DR2 archive

    twomass_cat:    (astropy.table.Table)
                    contains 2MASS data from IPAC in table form

    wise_cat:       (astropy.table.Table)
                    contains WISE data from IPAC in table form

    instrument:     (str)
                    Name of the instrument for which filter magnitudes are
                    needed:  "NIRcam", "NIRISS", "Guider", or "All"

    filter_names:   (list of str) or an empty list or None
                    List of names  of the filters to select for the instrument.
                    If the list is empty, or the value is None, all filters are
                    selected.

    Return values:

    outcat:         (mirage.catalogs.create_catalog.PointSourceCatalog object)
                    This is the catalog of positions/magnitudes.

    Note it is implicitly assumed that the GAIA/2MASS/WISE data are for the
    same area of sky.

    The code gives different results depending on what magnitudes are available.

    If only the GAIA g magnitude is available, this is used for all filters.

    If only the GAIA g/BP/RP magnitudes are available, the BP - RP magnitude
    value is used to predict the infrared magnitudes based on standard stellar
    atmosphere simulations.

    If any 2MASS or WISE magnitudes (excluding upper limits) are available the
    JWST magnitudes are found by wavelength interpolation using the pivot
    wavelengths of the different filters including those for GAIA/2MASS/WISE.
    """
    standard_magnitudes, standard_values, standard_filters, standard_labels = read_standard_magnitudes()
    nfilters = len(filter_names)
    ngaia = len(gaia_cat['ra'])
    n2mass1 = len(gaia_2mass_crossref['ra'])
    nwise1 = len(gaia_wise_crossref['ra'])
    n2mass2 = len(twomass_cat['ra'])
    nwise2 = len(wise_cat['ra'])
    nout = ngaia + (n2mass2 - n2mass1) + (nwise2 - nwise1)
    match1 = len(gaia_2mass_crossref)
    match2 = len(gaia_wise_crossref)
    in_magnitudes = np.zeros((nout, 10), dtype=np.float32) + 10000.0
    raout = np.zeros((nout), dtype=np.float32)
    decout = np.zeros((nout), dtype=np.float32)
    # magnitudes Gaia bp, g, rp; 2MASS J, H, Ks; WISE W1, W2, W3, W4
    in_filters = ['GAIA gbp', 'GAIA g ', 'GAIA grp', '2MASS J', '2MASS H',
                  '2MASS Ks', 'WISE W1', 'WISE W2', 'WISE W3', 'WISE W4']
    inds = crossmatch_filter_names(in_filters, standard_filters)
    if len(inds) != len(in_filters):
        print('Error matching the filters to the standard set.')
        return None
    # first populate the gaia sources, with cross-references
    in_magnitudes[0:ngaia, 1] = gaia_cat['phot_g_mean_mag']
    raout[0:ngaia] = gaia_cat['ra']
    decout[0:ngaia] = gaia_cat['dec']
    matchwise, gaiawiseinds = wise_crossmatch(gaia_cat, gaia_wise, gaia_wise_crossref, wise_cat)
    # dummy_value = np.zeros((1), dtype=np.float64)
    wisekeys = ['w1sigmpro', 'w2sigmpro', 'w3sigmpro', 'w4sigmpro']
    for loop in range(ngaia):
        try:
            in_magnitudes[loop, 0] = gaia_cat['phot_bp_mean_mag'][loop]
            in_magnitudes[loop, 2] = gaia_cat['phot_rp_mean_mag'][loop]
        except:
            pass
        for n1 in range(match1):
            if gaia_cat['designation'][loop] == gaia_2mass_crossref['designation'][n1]:
                in_magnitudes[loop, 3] = gaia_2mass['j_m'][n1]
                in_magnitudes[loop, 4] = gaia_2mass['h_m'][n1]
                in_magnitudes[loop, 5] = gaia_2mass['ks_m'][n1]
                for l1 in range(3):
                    if gaia_2mass['ph_qual'][n1][l1] == 'U':
                        in_magnitudes[loop, 3+l1] = 10000.
        if matchwise[loop]:
            in_magnitudes[loop, 6] = wise_cat['w1mpro'][gaiawiseinds[loop]]
            in_magnitudes[loop, 7] = wise_cat['w2mpro'][gaiawiseinds[loop]]
            in_magnitudes[loop, 8] = wise_cat['w3mpro'][gaiawiseinds[loop]]
            in_magnitudes[loop, 9] = wise_cat['w4mpro'][gaiawiseinds[loop]]
            for l1 in range(4):
                if not isinstance(wise_cat[wisekeys[l1]][gaiawiseinds[loop]], float):
                #if type(wise_cat[wisekeys[l1]][gaiawiseinds[loop]]) != type(dummy_value[0]):
                    in_magnitudes[loop, 6+l1] = 10000.
    # locate any 2MASS and WISE sources not in the cross references
    match2mass = []
    match2masstowise = []
    for loop in range(n2mass2):
        match2mass.append(False)
    for loop in range(n2mass2):
        for l1 in range(n2mass1):
            if gaia_2mass['designation'][l1] == twomass_cat['designation'][loop]:
                match2mass[loop] = True
                break
    # find the nearest position matches from 2MASS to WISE and vice versa
    ra1 = np.copy(twomass_cat['ra'])
    dec1 = np.copy(twomass_cat['dec'])
    ra2 = np.copy(wise_cat['ra'])
    dec2 = np.copy(wise_cat['dec'])
    sc1 = SkyCoord(ra=ra1*u.degree, dec=dec1*u.degree)
    sc2 = SkyCoord(ra=ra2*u.degree, dec=dec2*u.degree)
    idx1, d2d1, d3d1 = sc1.match_to_catalog_sky(sc2)
    idx2, d2d2, d3d2 = sc2.match_to_catalog_sky(sc1)
    # Now populate the 2MASS sources that are not in the GAIA cross-reference,
    # with cross-referece to WISE where the position match is < 0.4 arc-seconds.
    matchwise1 = []
    for loop in range(len(wise_cat['ra'])):
        matchwise1.append(False)
    for loop in range(len(matchwise)):
        if matchwise[loop]:
            matchwise1[gaiawiseinds[loop]] = True
    n1 = 0
    for loop in range(n2mass2):
        if not match2mass[loop]:
            arcdist = d2d1[loop].arcsec
            in_magnitudes[ngaia+n1, 3] = twomass_cat['j_m'][loop]
            in_magnitudes[ngaia+n1, 4] = twomass_cat['h_m'][loop]
            in_magnitudes[ngaia+n1, 5] = twomass_cat['k_m'][loop]
            raout[ngaia+n1] = twomass_cat['ra'][loop]
            decout[ngaia+n1] = twomass_cat['dec'][loop]
            for l1 in range(3):
                if twomass_cat['ph_qual'][loop][l1] == 'U':
                    in_magnitudes[ngaia+n1, 3+l1] = 10000.
            if arcdist < 0.4:
                if matchwise1[idx1[loop]] is not True:
                    matchwise1[idx1[loop]] = True
                    in_magnitudes[ngaia+n1, 6] = wise_cat['w1mpro'][idx1[loop]]
                    in_magnitudes[ngaia+n1, 7] = wise_cat['w2mpro'][idx1[loop]]
                    in_magnitudes[ngaia+n1, 8] = wise_cat['w3mpro'][idx1[loop]]
                    in_magnitudes[ngaia+n1, 9] = wise_cat['w3mpro'][idx1[loop]]
                    for l1 in range(4):
                        if not isinstance(wise_cat[wisekeys[l1]][idx1[loop]], float):
                        #if type(wise_cat[wisekeys[l1]][idx1[loop]]) != type(dummy_value[0]):
                            in_magnitudes[ngaia+n1, 6+l1] = 10000.
            n1 = n1+1
    # Finally, add in WISE sources that have not been cross-matched.
    noff = ngaia+n1
    n1 = 0
    for loop in range(nwise2):
        if not matchwise1[loop]:
            raout[noff+n1] = wise_cat['ra'][loop]
            decout[noff+n1] = wise_cat['dec'][loop]
            in_magnitudes[noff+n1, 6] = wise_cat['w1mpro'][loop]
            in_magnitudes[noff+n1, 7] = wise_cat['w2mpro'][loop]
            in_magnitudes[noff+n1, 8] = wise_cat['w3mpro'][loop]
            in_magnitudes[noff+n1, 9] = wise_cat['w3mpro'][loop]
            for l1 in range(4):
                if not isinstance(wise_cat[wisekeys[l1]][loop], float):
                #if type(wise_cat[wisekeys[l1]][loop]) != type(dummy_value[0]):
                    in_magnitudes[noff+n1, 6+l1] = 10000.
            n1 = n1+1
    # Now, convert to JWST magnitudes either by transformation (for sources
    # with GAIA G/BP/RP magnitudes) or by interpolation (all other
    # cases).
    out_magnitudes = np.zeros((nout, nfilters), dtype=np.float32)
    out_filter_names = make_filter_names(instrument, filter_names)
    inds = crossmatch_filter_names(in_filters, standard_filters)
    in_wavelengths = np.squeeze(np.copy(standard_values[0, inds]))
    inds = crossmatch_filter_names(out_filter_names, standard_filters)
    if len(inds) < 1:
        return None
    out_wavelengths = np.squeeze(np.copy(standard_values[0, inds]))
    if len(inds) == 1:
        out_wavelengths = np.zeros((1), dtype=np.float32)+out_wavelengths
    nfinal = noff + n1
    for loop in range(nfinal):
        values = interpolate_magnitudes(in_wavelengths, in_magnitudes[loop, :],
                                        out_wavelengths, out_filter_names)
        out_magnitudes[loop, :] = np.copy(values)
    raout = np.copy(raout[0:nfinal])
    decout = np.copy(raout[0:nfinal])
    out_magnitudes = np.copy(out_magnitudes[0:nfinal, :])
    outcat = PointSourceCatalog(ra=raout, dec=decout)
    n1 = 0
    for filter in out_filter_names:
        values = filter.split('_')
        if len(values) == 3:
            inst = values[0].upper()
            fil1 = values[1].upper()
        else:
            inst = values[0].upper()
            fil1 = ''
        outcat.add_magnitude_column(np.squeeze(out_magnitudes[:, n1]), instrument=inst,
                                    filter_name=fil1, magnitude_system='vegamag')
        n1 = n1+1
    return outcat


def wise_crossmatch(gaia_cat, gaia_wise, gaia_wise_crossref, wise_cat):
    """
    Relate the GAIA/WISE designations to the WISE catalogue designations, since the names
    change a little between the different catalogues.  Return the boolean list of matches and
    the index values in wise_cat.

    Input values:

    gaia_cat :   (astropy.table.Table)
                 contains the GAIA DR2 catalogue values from the GAIA aarchive

    gaia_wise :  (astropy.table.Table)
                 contains WISE catalogue values from the GAIA DR2 archive

    gaia_wise_crossref :   (astropy.table.Table)
                           contains GAIA/WISE cross-references from the GAIA DR2 archive

    wise_cat :      (astropy.table.Table)
                    contains WISE data from IPAC in table form

    Return values:

    matchwise :     (list of Booleans)
                    list of length equal to wise_cat with True if there is a cross-match with GAIA

    gaiawiseinds :  (list of int)
                    list of index values from gaia_cat to wise_cat

    """
    matchwise = []
    gaiawiseinds = []
    for loop in range(len(wise_cat['ra'])):
        matchwise.append(False)
        gaiawiseinds.append(-1)
    ra1 = np.copy(wise_cat['ra'])
    dec1 = np.copy(wise_cat['dec'])
    ra2 = np.copy(gaia_wise['ra'])
    dec2 = np.copy(gaia_wise['dec'])
    sc1 = SkyCoord(ra=ra1*u.degree, dec=dec1*u.degree)
    sc2 = SkyCoord(ra=ra2*u.degree, dec=dec2*u.degree)
    idx, d2d, d3d = sc2.match_to_catalog_sky(sc1)
    for loop in range(len(gaia_wise_crossref['ra'])):
        for n1 in range(len(gaia_cat['ra'])):
            if gaia_cat['designation'][n1] == gaia_wise_crossref['designation'][loop]:
                matchwise[n1] = True
                for n2 in range(len(gaia_wise['ra'])):
                    if gaia_wise['designation'][n2] == gaia_wise_crossref['designation_2'][loop]:
                        gaiawiseinds[n1] = idx[n2]
                        break
    return matchwise, gaiawiseinds


def interpolate_magnitudes(wl1, mag1, wl2, filternames):
    """
    Given an input set of magnitudes and associated wavelengths, interpolate
    these in wavelength to get approximate JWST magnitudes.  It is assumed that
    the first 3 magnitudes in the input vector mag1 are the GAIA BP, g, and
    RP filters and that the rest are long wavelength magnitudes.  If only the
    GAIA g filter magnitude is available it is used for all output magnitudes.
    If only GAIA BP/g/RP magnitudes are available the GAIA BP/RP magnitudes
    are transformed to JWST magnitudes based on stellar model values.  In the
    case where there is some infrared data, the numpy interp function is used
    to interpolate the magnitudes.  In the inputs filters without data are
    assigned magnitude > 100, and these are not used in the interpolation.
    As is normal for numpy interp, wavelength values outside the defined
    range in the input magnitudes get nearest magnitude value.

    The input magnitudes are

    Input values:

    wl1:      (numpy vector of floats)
              The pivot wavelengths, in microns, for the input filters.  The
              values need to be sorted before passing to the routine.

    mag1:     (numpy vector of floats)
              The associated magnitudes (A0V by assumption).  Values > 100.
              indicate "no data".

    wl2:      (numpy vector of floats)
              The pivot wavelengths, in microns, for the output filters

    filternames:   (list of str)
                   The names of the output filters, used when the GAIA blue/red
                   magnitudes are available but no near-infrared magnitudes
                   are available.

    Return values:

    out_magnitudes:  (numpy vector of floats)
                     The output interpolated magnitudes corresponding to the
                     wavelengths.
    """
    nout = len(wl2)
    outmags = wl2*0.+10000.
    # Case 1:  All dummy values, return all magnitudes = 10000.0 (this should
    #          not happen)
    if np.min(mag1) > 100.:
        return outmags
    # Case 2,  Only GAIA magnitudes.  Either return all magnitudes = GAIA g
    #          if that is the only magnitude, or transform BP - RP.
    if np.min(mag1[3:]) > 100.:
        if mag1[0] > 100.:
            outmags = wl2 * 0. + mag1[1]
            return outmags
        else:
            standard_magnitudes, standard_values, standard_filters, standard_labels = read_standard_magnitudes()
            inmags = np.copy(mag1[[0, 2]])
            in_filters = ['GAIA gbp', 'GAIA grp']
            newmags = match_model_magnitudes(inmags, in_filters, standard_magnitudes, standard_values,
                                             standard_filters, standard_labels)
            inds = crossmatch_filter_names(filternames, standard_filters)
            outmags = np.copy(newmags[inds])
            return outmags
    # Case 3, some infrared magnitudes are available, interpolate good values
    # (magnitude = 10000 for bad values)
    inds = np.where(mag1 < 100.)
    inmags = mag1[inds]
    inwl = wl1[inds]
    outmags = np.interp(wl2, inwl, inmags)
    return outmags


def make_filter_names(instrument, filters):
    """
    Given as input the instrument name and the list of filters needed, this
    routine generates the list of output header values for the Mirage input
    file.

    Inputs:

    insrument:   (string)  'NIRCam', 'NIRISS', or 'Guider"
    filters:     (list of strings) List of the filters needed (names such as
                 F090W) or either None or an empty list to select all filters)

    returns:

    headerstrs:  (list of strings) The header string list for the output Mirage
                 magnitudes line; if concatentated with spaces, it is the list
                 of magnitudes header values that needs to be written to the
                 source list file.

    """
    instrument_names = ['Guider', 'NIRCam', 'NIRISS']
    guider_filters = ['guider1', 'gauider2']
    guider_filter_names = ['guider1_magnitude', 'guider2_magnitude']
    niriss_filters = ['F090W', 'F115W', 'F140M', 'F150W', 'F158M', 'F200W',
                      'F277W', 'F356W', 'F380M', 'F430M', 'F444W', 'F480M']
    niriss_filter_names = ['niriss_f090w_magnitude', 'niriss_f115w_magnitude',
                           'niriss_f140w_magnitude', 'niriss_f150w_magnitude',
                           'niriss_f158w_magnitude', 'niriss_f200w_magnitude',
                           'niriss_f277w_magnitude', 'niriss_f356w_magnitude',
                           'niriss_f380w_magnitude', 'niriss_f430w_magnitude',
                           'niriss_f444w_magnitude', 'niriss_f480w_magnitude']
    nircam_filters = ['F070W', 'F090W', 'F115W', 'F140W', 'F150W', 'F150W2',
                      'F162W', 'F164W', 'F182W', 'F187W', 'F200W', 'F210W',
                      'F212W', 'F250W', 'F277W', 'F300W', 'F322W2', 'F323W',
                      'F335W', 'F356W', 'F360W', 'F405W', 'F410W', 'F430W',
                      'F444W', 'F460W', 'F466W', 'F470W', 'F480W']
    nircam_filter_names = ['nircam_f070w_magnitude', 'nircam_f090w_magnitude',
                           'nircam_f115w_magnitude', 'nircam_f140w_magnitude',
                           'nircam_f150w_magnitude', 'nircam_f150w2_magnitude',
                           'nircam_f162w_magnitude', 'nircam_f164w_magnitude',
                           'nircam_f182w_magnitude', 'nircam_f187w_magnitude',
                           'nircam_f200w_magnitude', 'nircam_f210w_magnitude',
                           'nircam_f212w_magnitude', 'nircam_f250w_magnitude',
                           'nircam_f277w_magnitude', 'nircam_f300w_magnitude',
                           'nircam_f322w2_magnitude', 'nircam_f323w_magnitude',
                           'nircam_f335w_magnitude', 'nircam_f356w_magnitude',
                           'nircam_f360w_magnitude', 'nircam_f405w_magnitude',
                           'nircam_f410w_magnitude', 'nircam_f430w_magnitude',
                           'nircam_f444w_magnitude', 'nircam_f460w_magnitude',
                           'nircam_f466w_magnitude', 'nircam_f470w_magnitude',
                           'nircam_f480w_magnitude']
    names1 = [guider_filters, nircam_filters, niriss_filters]
    names2 = [guider_filter_names, nircam_filter_names, niriss_filter_names]
    headerstrs = []
    for loop in range(len(instrument_names)):
        if (instrument_names[loop].lower() == instrument.lower()) or (instrument.lower() == 'all'):
            headerstrs = add_filter_names(headerstrs, names1[loop], names2[loop], filters)
    return headerstrs


def add_filter_names(headerlist, filter_names, filter_labels, filters):
    """
    Add a set of filter header labels (i.e. niriss_f090w_magnitude for example)
    to a list, by matching filter names.

    Inputs:

    headerlist:  (list)  An existing (possibly empty) list to hold the header
                         string for the output magnitudes

    filter_names:  (list)  The list of available filter names to match to

    filter_labels:  (list)  The corresponding list of filter labels

    filters:   (list)  The list of filter names to match, or an empty list or
                       None to get all available filter labels


    Return values:

    headerlist:  (list)  The revised list of labels with the filter labels
                         requested appended

    """
    try:
        n1 = len(filters)
    except:
        n1 = 0
    if (filters is None) or (n1 == 0):
        for loop in range(len(filter_labels)):
            headerlist.append(filter_labels[loop])
    if n1 > 0:
        for loop in range(n1):
            for k in range(len(filter_names)):
                if filters[loop].lower() == filter_names[k].lower():
                    headerlist.append(filter_labels[k])
    return headerlist


def combine_catalogs(observed_jwst, besancon_jwst):
    """
    This code takes two input PointSourceCatalog objects and returns the
    combined PointSourceCatalog.  The two catalogs have to be in the same
    magnitude units and have the same set of filters.

    Input values:

    observed_jwst:    (mirage.catalogs.catalog_generator.PointSourceCatalog)
                      Catalog object one

    besancon_jwst:    (mirage.catalogs.catalog_generator.PointSourceCatalog)
                      Catalog object two

    Return value:

    outcat:           (mirage.catalogs.catalog_generator.PointSourceCatalog)
                      A new catalog object combining the two input catalogs

    """
    keys1 = list(observed_jwst.magnitudes.keys())
    keys2 = list(besancon_jwst.magnitudes.keys())
    besanconinds = []
    for key in keys1:
        for loop in range(len(keys2)):
            if key == keys2[loop]:
                besanconinds.append(loop)
    if len(keys1) != len(besanconinds):
        print('Magnitude mismatch in catalogs to combine.  Will return None.')
        return None
    if observed_jwst.location_units != besancon_jwst.location_units:
        print('Coordinate mismatch in catalogs to combine.  Will return None.')
        return None
    ra1 = observed_jwst.ra
    dec1 = observed_jwst.dec
    ra2 = besancon_jwst.ra
    dec2 = besancon_jwst.dec
    raout = np.concatenate((ra1, ra2))
    decout = np.concatenate((dec1, dec2))
    outcat = PointSourceCatalog(ra=raout, dec=decout)
    outcat.location_units = observed_jwst.location_units
    for key in keys1:
        mag1 = observed_jwst.magnitudes[key][1]
        mag2 = besancon_jwst.magnitudes[key][1]
        magout = np.concatenate((mag1, mag2))
        values = key.split('_')
        instrument = values[0]
        filter = values[1]
        outcat.add_magnitude_column(magout, magnitude_system=observed_jwst.magnitudes[key][0],
                                    instrument=instrument, filter_name=filter)
    return outcat


def get_gaia_ptsrc_catalog(ra, dec, box_width):
    """Wrapper around Gaia query and creation of mirage-formatted catalog"""
    gaia_cat, gaia_mag_cols, gaia_2mass, gaia_2mass_crossref, gaia_wise, \
        gaia_wise_crossref = query_GAIA_ptsrc_catalog(ra, dec, box_width)
    gaia_mirage = mirage_ptsrc_catalog_from_table(gaia_cat, 'gaia', gaia_mag_cols)
    return gaia_mirage, gaia_cat, gaia_2mass_crossref, gaia_wise_crossref


def query_GAIA_ptsrc_catalog(ra, dec, box_width):
    """
    This code is adapted from gaia_crossreference.py by Johannes Sahlmann.  It
    queries the GAIA DR2 archive for sources within a given square region of
    the sky and rerurns the catalogue along withe the 2MASS and WISE
    cross-references for use in combining the catalogues to get the infrared
    magnitudes for the sources that are detected in the other telescopes.

    Input values:

    ra:         (float)
                right ascension of the target field in degrees
    dec:        (float)
                declination of the target field in degrees
    box_width:  (float)
                width of the (square) sky area, in arc-seconds

    Returns:

    gaia_cat:             (astropy.table.Table)
                          the gaia DR2 magnitudes and other data
    gaia_mag_cols:        (list)
                          a list of the GAIA magnitude column names
    gaia_2mass:           (astropy.table.Table)
                          the 2MASS values as returned from the GAIA archive
    gaia_2mass_crossref:  (astropy.table.Table)
                          the cross-reference list with 2MASS sources
    gaia_wise:            (astropy.table.Table)
                          the WISE values as returned from the GAIA archive
    gaia_wise_crossref:   (astropy.table.Table)
                          the cross-reference list with WISE sources

    The GAIA main table has all the GAIA values, but the other tables have only
    specific subsets of the data values to save space.  In the "crossref"
    tables the 'designation' is the GAIA name while 'designation_2' is the
    2MASS or WISE name.

    """
    data = OrderedDict()
    data['gaia'] = OrderedDict()
    data['tmass'] = OrderedDict()
    data['wise'] = OrderedDict()
    data['tmass_crossmatch'] = OrderedDict()
    data['wise_crossmatch'] = OrderedDict()
    # convert box width to degrees for the GAIA query
    boxwidth = box_width/3600.
    data['gaia']['query'] = """SELECT * FROM gaiadr2.gaia_source AS gaia
                        WHERE 1=CONTAINS(POINT('ICRS',gaia.ra,gaia.dec), BOX('ICRS',{}, {}, {}, {}))
                        """.format(ra, dec, boxwidth, boxwidth)

    data['tmass']['query'] = """SELECT ra,dec,ph_qual,j_m,h_m,ks_m,designation FROM gaiadr1.tmass_original_valid AS tmass
                        WHERE 1=CONTAINS(POINT('ICRS',tmass.ra,tmass.dec), BOX('ICRS',{}, {}, {}, {}))
                        """.format(ra, dec, boxwidth, boxwidth)

    data['tmass_crossmatch']['query'] = """SELECT field.ra,field.dec,field.designation,tmass.designation from
            (SELECT gaia.*
            FROM gaiadr2.gaia_source AS gaia
            WHERE 1=CONTAINS(POINT('ICRS',gaia.ra,gaia.dec), BOX('ICRS',{}, {}, {}, {})))
            AS field
            INNER JOIN gaiadr2.tmass_best_neighbour AS xmatch
                ON field.source_id = xmatch.source_id
            INNER JOIN gaiadr1.tmass_original_valid AS tmass
                ON tmass.tmass_oid = xmatch.tmass_oid
        """.format(ra, dec, boxwidth, boxwidth)

    data['wise']['query'] = """SELECT ra,dec,ph_qual,w1mpro,w2mpro,w3mpro,w4mpro,designation FROM gaiadr1.allwise_original_valid AS wise
                        WHERE 1=CONTAINS(POINT('ICRS',wise.ra,wise.dec), BOX('ICRS',{}, {}, {}, {}))
                        """.format(ra, dec, boxwidth, boxwidth)

    data['wise_crossmatch']['query'] = """SELECT field.ra,field.dec,field.designation,allwise.designation from
            (SELECT gaia.*
            FROM gaiadr2.gaia_source AS gaia
            WHERE 1=CONTAINS(POINT('ICRS',gaia.ra,gaia.dec), BOX('ICRS',{}, {}, {}, {})))
            AS field
            INNER JOIN gaiadr2.allwise_best_neighbour AS xmatch
                ON field.source_id = xmatch.source_id
            INNER JOIN gaiadr1.allwise_original_valid AS allwise
                ON allwise.designation = xmatch.original_ext_source_id
        """.format(ra, dec, boxwidth, boxwidth)

    outvalues = {}
    print('Searching the GAIA DR2 catalog')
    for key in data.keys():
        job = Gaia.launch_job_async(data[key]['query'], dump_to_file=False)
        table = job.get_results()
        outvalues[key] = table
        print('Retrieved {} sources for catalog {}'.format(len(table), key))
    gaia_mag_cols = ['phot_g_mean_mag', 'phot_bp_mean_mag', 'phot_rp_mean_mag']
    return outvalues['gaia'], gaia_mag_cols, outvalues['tmass'], outvalues['tmass_crossmatch'], outvalues['wise'], outvalues['wise_crossmatch']


def besancon(ra, dec, box_width, coords='ra_dec', email='', kmag_limits=(13, 29)):
    """
    This routine calls a server to get a Besancon star count model over a given
    small sky area at a defined position.  For documentation of the Besancon
    model see the web site: http://model.obs-besancon.fr/

    The star count model returns V, J, H, K, and L magnitudes plus other
    information.  Here the magnitudes and the extinction are of most interest
    in producing the simulated NIRISS/NIRCam/Guider magnitudes.

    Note that the Besancon model uses a simplified exinction model, and so
    this is carried over into the Mirage point source lists.

    An email address is required for the besancon call.

    Input quantities:

        ra            the right ascension or galactic longitude for the sky
                      position where the model is to be calculated, in degrees.
                      Which it is depends on the "coords" parameter.
                      (float)

        dec           the declinatino or galactic latitude for the sky
                      position where the model is to be calculated, in degrees.
                      Which it is depends on the "coords" parameter.
                      (float)

        box_width     the size of the (square) sky area to be simulated, in
                      arc-seconds
                      (float)

        coords        an optional string parameter; if it is "ra_dec", the
                      default value, then the input values are assumed to
                      be RA/Dec in degrees.  Otherwise the values are assumed
                      to be (l,b) in degrees.
                      (string)

        kmag_limits   the range of allowable K magnitudes for the model, given
                      as a tuple (min, max).  The default is (13,29).  The
                      bright limit will generally be set by 2MASS completeness
                      limit.  The 2MASS faint limit for any given sky position
                      is roughly magnitude 15 to 16 in general.  As the 2MASS
                      completeness limit varies with position and the
                      completeness limit is above the faint limit the Besancon
                      bright limit is taken as magnitude 14 by default.  Note
                      that for the JWST instruments the 2MASS sources will
                      saturate in full frame imaging in many cases.
                      (tuple)

    Return values:

        cat     a table object containing the simulated (random) sky positions
                within the field and the associated VJHKL magnitudes.
                (obj)
                mirage.catalogs.create_catalog.PointSourceCatalog

        model   the full Besancon model table for the query.
                (astropy.table.Table)

    """
    from astroquery.besancon import Besancon
    from astropy import units as u
    from astropy.coordinates import SkyCoord

    # Specified coordinates. Will need to convert to galactic long and lat
    # when calling model
    ra = ra * u.deg
    dec = dec * u.deg
    box_width = box_width * u.arcsec

    if coords == 'ra_dec':
        location = SkyCoord(ra=ra, dec=dec, frame='icrs')
        coord1 = location.galactic.l.value
        coord2 = location.galactic.b.value
    elif coords == 'galactic':
        coord1 = ra.value
        coord2 = dec.value

    # Area of region to search (model expects area in square degrees)
    area = box_width * box_width
    area = area.to(u.deg * u.deg)

    # Query the model
    model = Besancon.query(coord1, coord2, smallfield=True, area=area.value,
                           colors_limits={"J-H": (-99, 99), "J-K": (-99, 99),
                                          "J-L": (-99, 99), "V-K": (-99, 99)},
                           mag_limits={'U': (-99, 99), 'B': (-99, 99), 'V': (-99, 99),
                                       'R': (-99, 99), 'I': (-99, 99), 'J': (-99, 99),
                                       'H': (-99, 99), 'K': kmag_limits, 'L': (-99, 99)},
                           retrieve_file=True, email=email)

    # Calculate magnitudes in given bands
    v_mags = model['V'].data
    k_mags = (model['V'] - model['V-K']).data
    j_mags = k_mags + model['J-K'].data
    h_mags = j_mags - model['J-H'].data
    l_mags = j_mags - model['J-L'].data

    # Since these are theoretical stars generated by a model, we need to provide RA and Dec values.
    # The model is run in 'smallfield' mode, which assumes a constant density of stars across the given
    # area. So let's just select RA and Dec values at random across the fov.
    half_width = box_width * 0.5
    min_ra = ra - half_width
    max_ra = ra + half_width
    min_dec = dec - half_width
    max_dec = dec + half_width
    ra_values, dec_values = generate_ra_dec(len(k_mags), min_ra, max_ra, min_dec, max_dec)

    # Create the catalog object
    cat = PointSourceCatalog(ra=ra_values, dec=dec_values)

    # Add the J, H, K and L magnitudes as they may be useful for magnitude conversions later
    cat.add_magnitude_column(v_mags, instrument='Besancon', filter_name='v', magnitude_system='vegamag')
    cat.add_magnitude_column(j_mags, instrument='Besancon', filter_name='j', magnitude_system='vegamag')
    cat.add_magnitude_column(h_mags, instrument='Besancon', filter_name='h', magnitude_system='vegamag')
    cat.add_magnitude_column(k_mags, instrument='Besancon', filter_name='k', magnitude_system='vegamag')
    cat.add_magnitude_column(l_mags, instrument='Besancon', filter_name='l', magnitude_system='vegamag')
    nstars = len(cat.ra)
    print('The Besancon model contains %d stars.' % (nstars))
    return cat, model


def galactic_plane(box_width, email=''):
    """Convenience function to create a typical scene looking into the disk of
    the Milky Way, using the besancon function

    Parameters
    ----------
    box_width : float

    Returns
    -------
    cat : obj
        mirage.catalogs.create_catalog.PointSourceCatalog

    model:  table object

    RA and Dec values of various features

    Center of MW
    center_ra = 17h45.6m
    center_dec = -28.94 deg

    anti-center-ra = 5h45.6m
    anti-center-dec = 28.94deg

    Galactic Poles
    north_pole_ra = 12h51.4m
    north_pole_dec = 27.13deg

    south_pole_ra = 0h51.4m
    south_pole_dec = -27.13deg
    """
    representative_galactic_longitude = 45.0  # deg
    representative_galactic_latitude = 0.0  # deg

    cat, model = besancon(representative_galactic_longitude, representative_galactic_latitude,
                          box_width, coords='galactic', email=email)
    return cat, model


def out_of_plane(box_width, email=''):
    """Convenience function to create typical scene looking out of the plane of
    the Milky Way

    Parameters
    ----------
    box_width : float

    Returns
    -------
    cat : obj
        mirage.catalogs.create_catalog.PointSourceCatalog

    model : table object
    """
    representative_galactic_longitude = 45.0  # deg
    representative_galactic_latitude = 85.0  # deg

    cat = besancon(representative_galactic_longitude, representative_galactic_latitude,
                   box_width, coords='galactic', email=email)
    return cat


def galactic_bulge(box_width, email=''):
    """Convenience function to create typical scene looking into bulge of
    the Milky Way

    Parameters
    ----------
    box_width : float

    Returns
    -------
    cat : obj
        mirage.catalogs.create_catalog.PointSourceCatalog
    model:  table object
    """
    #Look up Besancon limitations. Model breaks down somewhere close to the
    #galactic core.
    representative_galactic_longitude = 0.  # ? deg
    representative_galactic_latitude = 5.0  # ? deg

    cat, model = besancon(representative_galactic_longitude, representative_galactic_latitude,
                          box_width, coords='galactic', email=email)
    return cat, model

#def from_luminosity_function(self, luminosity_function):
#    more customizable


def filter_bad_ra_dec(table_data):
    """Use the column masks to find which entries have bad RA or Dec values.
    These will be excluded from the Mirage catalog

    Parameters
    ----------
    something

    Returns
    -------

    position_mask : np.ndarray
        1D boolean array. True for good sources, False for bad.
    """
    #ra_data = table_data['ra'].data.data
    ra_mask = ~table_data['ra'].data.mask
    #dec_data = table_data['dec'].data.data
    dec_mask = ~table_data['dec'].data.mask
    position_mask = ra_mask & dec_mask
    return position_mask


def generate_ra_dec(number_of_stars, ra_min, ra_max, dec_min, dec_max):
    """
    Generate a list of random RA, Dec values in a square region.  Note that
    this assumes a small sky area so that the change in the sky area per
    a degree of right ascension is negligible.  This routine will break down
    at the north or south celestial poles.

    The np uniform random number generator is used to make the source
    postions.  Since the seed value is not set or recorded, the values cannot
    be reproduced from one call to another.

    Input values:

        number_of_stars:  (int) The number of stars in the field.

        ra_min:           (float) The minimum RA value of the area, in degrees

        ra_max:           (float) The maximum RA value of the area, in degrees

        dec_min:          (float) The minimum Dec value of the area, in degrees

        dec_max:          (float) The minimum Dec value of the area, in degrees

    Return values:

        ra_list:     (np array)  The list of output RA values in degrees.

        dec_list:    (np array)  The list of output Dec values in degrees.


    """
    delta_ra = ra_max - ra_min
    ra_list = np.random.random(number_of_stars) * delta_ra + ra_min
    delta_dec = dec_max - dec_min
    dec_list = np.random.random(number_of_stars) * delta_dec + dec_min
    return ra_list, dec_list


def galaxy_background(ra0, dec0, v3rotangle, box_width, instrument, filters,
                      boxflag=True, brightlimit=14.0, seed=None):
    """
    Given a sky position (ra0,dec0), and a V3 rotation angle (v3rotangle) this
    routine makes a fake galaxy background for a square region of sky or a circle
    provided that the area is smaller than the GODDS-S field.  The fake galaxies
    are randomly distributed over the area and have random changes to the input
    Sersic parameters, so the field is different at every call.

    Input values:

    ra0 :        (float)
                 the sky position right ascension in decimal degrees

    dec0 :       (float)
                 the sky position declimation in decimal degrees

    v3rotangle : (float)
                 the v3 rotation angle of the y coordinate in the image, in
                 degrees E of N

    box_width :  (float)
                 the width of the square on the sky in arc-seconds, or the
                 radius of the circle on the sky in arc-seconds; must be a
                 value larger and 1.0 and smaller than 779.04 for a square
                 or 439.52 for a circle.

    boxflag :    (boolean)
                 Flag for whether the region is a square (if True) or a
                 circle (if False).

    instrument :  (str)
                  One of "All", "NIRCam", "NIRISS", or "Guider".

    filters :     (list of str)
                  A list of the required filters.  If set to None or an empty
                  list all filters are used.

    brightlimit : (float)
                  The bright limit AB magnitude for the galaxies in the output
                  catalogue, applied in the F200W filter (close to K-band).

    seed :        (integer) or None
                  If a value is given, it is used to seed the random number
                  generator so that a scene can be reproduced.  If the value
                  is None the seed is set randomly.  If a non-integer value is
                  given it is converted to integer.

    Return values:

    galaxy_cat :  (mirage.catalogs.catalog_generate.GalaxyCatalog object)
                  This is the output list of galaxy properties.  If there is
                  an error, None is returned.

    seedvalue :   (integer)
                  The seed value used with numpy.random to generate the values.

    """
    # The following is the area of the GOODS-S field catalogue from Gabe Brammer
    # in square arc-seconds
    goodss_area = 606909.
    if boxflag:
        outarea = box_width*box_width
    else:
        outarea = math.pi*box_width*box_width
    if outarea >= goodss_area:
        print('Error: requested sky area is too large.  Values will not be produced.')
        return None, None
    if seed is None:
        seedvalue = int(950397468.*np.random.random())
    else:
        if not isinstance(seed, int):
            seedvalue = int(abs(seed))
        else:
            seedvalue = seed
    np.random.seed(seedvalue)
    threshold = outarea/goodss_area
    filter_names = make_filter_names(instrument, filters)
    nfilters = len(filter_names)
    if nfilters < 1:
        print('Error matching filters to standard list.  Inputs are:')
        print('Instrument: ', instrument)
        print('Filter names: ', filters)
        return None, None
    # add 8 to these indexes to get the columns in the GODDS-S catalogue file
    #
    # Note: NIRCam filters are used in proxy for the NIRISS long wavelength
    # filters.  The broad NIRCam F150W2 filter is used as a proxy for the
    # Guiders.
    filterinds = {'niriss_f090w_magnitude': 0, 'niriss_f115w_magnitude': 1,
                  'niriss_f150w_magnitude': 2, 'niriss_f200w_magnitude': 3,
                  'niriss_f140m_magnitude': 4, 'niriss_f158m_magnitude': 5,
                  'nircam_f070w_magnitude': 6, 'nircam_f090w_magnitude': 7,
                  'nircam_f115w_magnitude': 8, 'nircam_f150w_magnitude': 9,
                  'nircam_f200w_magnitude': 10, 'nircam_f150w2_magnitude': 11,
                  'nircam_f140m_magnitude': 12, 'nircam_f162m_magnitude': 13,
                  'nircam_f182m_magnitude': 14, 'nircam_f210m_magnitude': 15,
                  'nircam_f164n_magnitude': 16, 'nircam_f187n_magnitude': 17,
                  'nircam_f212n_magnitude': 18, 'nircam_f277w_magnitude': 19,
                  'nircam_f356w_magnitude': 20, 'nircam_f444w_magnitude': 21,
                  'nircam_f322w2_magnitude': 22, 'nircam_f250m_magnitude': 23,
                  'nircam_f300m_magnitude': 24, 'nircam_f335m_magnitude': 25,
                  'nircam_f360m_magnitude': 26, 'nircam_f410m_magnitude': 27,
                  'nircam_f430m_magnitude': 28, 'nircam_f460m_magnitude': 29,
                  'nircam_f480m_magnitude': 30, 'nircam_f323n_magnitude': 31,
                  'nircam_f405n_magnitude': 32, 'nircam_f466n_magnitude': 33,
                  'nircam_f470n_magnitude': 34, 'niriss_f277w_magnitude': 19,
                  'niriss_f356w_magnitude': 20, 'niriss_f380m_magnitude': 26,
                  'niriss_f430m_magnitude': 28, 'niriss_f444w_magnitude': 21,
                  'niriss_f480m_magnitude': 30, 'guider1_magnitude': 11,
                  'guider2_magnitude': 11}
    path = os.environ.get('MIRAGE_DATA')
    catalog_values = np.loadtxt(os.path.join(path, 'niriss/catalogs/', 'goodss_3dhst.v4.1.jwst_galfit.cat'),
                                comments='#')
    outinds = np.zeros((nfilters), dtype=np.int16)
    try:
        loop = 0
        for filter in filter_names:
            outinds[loop] = filterinds[filter] + 8
            loop = loop+1
    except:
        print('Error matching filter %s to standard list.' % (filter))
        return None, None
    # The following variables hold the Sersic profile index values
    # (radius [arc-seconds], sersic index, ellipticity, position angle)
    # and the assocated uncertaintie index values
    sersicinds = [59, 61, 63, 65]
    sersicerrorinds = [60, 62, 64, 66]
    ncat = catalog_values.shape[0]
    select = np.random.random(ncat)
    magselect = np.copy(catalog_values[:, filterinds['niriss_f200w_magnitude']+8])
    outputinds = []
    for loop in range(ncat):
        if (magselect[loop] >= brightlimit) and (select[loop] < threshold):
            outputinds.append(loop)
    nout = len(outputinds)
    if boxflag:
        delx0 = (-0.5+np.random.random(nout))*box_width/3600.
        dely0 = (-0.5+np.random.random(nout))*box_width/3600.
        radius = np.sqrt(delx0*delx0+dely0*dely0)
        angle = np.arctan2(delx0, dely0)+v3rotangle*math.pi/180.
    else:
        radius = box_width*np.sqrt(np.random.random(nout))/3600.
        angle = 2.*math.pi*np.random.random(nout)
    delx = radius*np.cos(angle)
    dely = radius*np.sin(angle)
    raout = delx * 0.
    decout = dely * 0.
    for loop in range(len(delx)):
        raout[loop], decout[loop] = distortion.Pix2RADec_TAN(delx[loop], dely[loop], ra0, dec0)
    rot1 = 360.*np.random.random(nout)-180.
    rout = np.copy(catalog_values[outputinds, sersicinds[0]])
    drout = np.copy(catalog_values[outputinds, sersicerrorinds[0]])
    rout = rout+2.*drout*np.random.normal(0., 1., nout)
    rout[rout < 0.01] = 0.01
    elout = np.copy(catalog_values[outputinds, sersicinds[2]])
    delout = np.copy(catalog_values[outputinds, sersicerrorinds[2]])
    elout = elout+delout*np.random.normal(0., 1., nout)
    elout[elout > 0.98] = 0.98
    sindout = np.copy(catalog_values[outputinds, sersicinds[1]])
    dsindout = np.copy(catalog_values[outputinds, sersicinds[1]])
    sindout = sindout+dsindout*np.random.normal(0., 1., nout)
    sindout[sindout < 0.1] = 0.1
    paout = np.copy(catalog_values[outputinds, sersicinds[3]])
    dpaout = np.copy(catalog_values[outputinds, sersicinds[3]])
    paout = paout+dpaout*np.random.normal(0., 1., nout)
    for loop in range(len(paout)):
        if paout[loop] < -180.:
            paout[loop] = paout[loop]+360.
        if paout[loop] > 180.:
            paout[loop] = paout[loop]-360.
    galaxy_cat = GalaxyCatalog(ra=raout, dec=decout, ellipticity=elout,
                               radius=rout, sersic_index=sindout,
                               position_angle=paout, radius_units='arcsec')
    galaxy_cat.location_units = 'position_RA_Dec'
    for loop in range(len(filter_names)):
        mag1 = catalog_values[outputinds, outinds[loop]]
        dmag1 = -0.2*np.random.random(nout)+0.1
        mag1 = mag1 + dmag1
        if 'niriss' in filter_names[loop]:
            inst1 = 'NIRISS'
            filter = filter_names[loop].strip('niriss_')
            filter = filter.strip('_magnitude')
            filter = filter.upper()
        elif 'nircam' in filter_names[loop]:
            inst1 = 'NIRCam'
            filter = filter_names[loop].strip('nircam_')
            filter = filter.strip('_magnitude')
            filter = filter.upper()
        else:
            inst1 = 'Guider'
            filter = filter_names.strip('_magnitude')
        galaxy_cat.add_magnitude_column(mag1, instrument=inst1,
                                        filter_name=filter,
                                        magnitude_system='abmag')
    return galaxy_cat, seedvalue
