import functools
from . import neucbot
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import LogNorm
import io
import base64
from colour import Color
import numpy as np
import pandas as pd

from flask import ( # type: ignore
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

bp = Blueprint('calc', __name__, url_prefix='/')

@bp.route('/', methods=('GET', 'POST'))
def calc():
    if request.method == 'POST':


        alphas = request.form.get('alpha_chain')
        if alphas == "":
            alphafile = request.files['alphafile']
            print(alphafile)
            alphas = neucbot.loadChainAlphaList(alphafile)
        else:
            alphas = neucbot.loadChainAlphaList(alphas)

        #####################################################
        mat = request.form.get('material')
        if mat == "":
            matfile = request.files['matfile']
            mat = neucbot.readTargetMaterial(matfile)
        else:
            mat = neucbot.readTargetMaterial(mat)
        slow_calc = request.form.get('a_energy_calculation')
        #####################################################
        if not alphas:
            flash('Input text is required')
            return redirect(url_for('calc.calc'))
        
        neucbot.constants.download_data = True
        neucbot.constants.run_talys = True
        neucbot.download_talys_data(mat)
        if(slow_calc == "True"):
            xsects, nspec, pspec, aspec, max_alpha, a_n_list, aspec_norm = neucbot.run_alpha_energy_loss(alphas, mat, .01)
            print("Print norm", aspec_norm)


            #blue = Color("blue")
            #colors = list(blue.range_to(Color("Yellow"),100))
            
            #create nspec graph
            fig, ax = plt.subplots()
            ax.plot(sorted(pspec.keys()),[pspec[k] for k in sorted(pspec.keys())], linestyle="-", color='g')
            ax.set_title("Neutron Emission Probability Spectrum")
            ax.set_xlabel("Neutron Energy")
            ax.set_ylabel("Probability")
            ax.grid()

            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            ngraph = base64.b64encode(buf.getvalue()).decode()

            graph_list = {}
            tuf = {}

            #Collect probability graph for each neutron energy
            for e in a_n_list:

                fig, nx = plt.subplots()
                nx.plot(sorted(a_n_list[e].keys()),[a_n_list[e][k] for k in sorted(a_n_list[e].keys())], linestyle="-", color='b')
                title = "(a,n) Spectrum for " + str(e) + " keV En"
                nx.set_title(title)
                nx.set_xlabel("ΔEα")
                nx.set_ylabel("Probability/keV")
                #plt.figure(figsize=(8,6))

                tuf[e] = io.BytesIO()
                plt.savefig(tuf[e], format="png")
                tuf[e].seek(0)
                graph_list[e] = base64.b64encode(tuf[e].getvalue()).decode()

            fig, tx = plt.subplots()

            max_prob = max(aspec_norm.values())

            #Create 2d histogram for probabilities, Alpha Energy vs Neutron Energy, normalized

            xbins = np.unique(sorted({key[0] for key in aspec_norm.keys()}))
            ybins = np.unique(sorted({key[1] for key in aspec_norm.keys()}))

            histogram_data = np.zeros((len(ybins), len(xbins)))

            for i, x in enumerate(xbins):
                for j, y in enumerate(ybins):
                    histogram_data[j, i] = aspec_norm.get((x, y), 0)

            # Plot using `pcolormesh`
            plt.figure(figsize=(8,6))
            hx = plt.pcolormesh( xbins, ybins, histogram_data, shading='nearest', cmap='inferno', norm = LogNorm(vmin=max_prob*1e-4, vmax=max_prob) )
            
            cbar = plt.colorbar(hx)

            plt.title("2d histogram")
            plt.xlabel("Neutron Energy(keV)")
            plt.ylabel("ΔEα(MeV)")

            suf = io.BytesIO()
            plt.savefig(suf,format="png")
            suf.seek(0)
            hist = base64.b64encode(suf.getvalue()).decode()


            return render_template('calc/calc.html', xsect = xsects,nspec = nspec, probspec = pspec, aspec = aspec, max_alpha = max_alpha, ngraph=ngraph, graph_list = graph_list, hist = hist, alphas_list = alphas, mat_list = mat)

        #######################################Short Calculation#########################################
        else:
            xsects, nspec, pspec = neucbot.run_alpha(alphas, mat, .01)

            fig, ax = plt.subplots()
            ax.plot(sorted(pspec.keys()),[pspec[k] for k in sorted(pspec.keys())], linestyle="-", color='g')
            ax.set_title("Neutron Emission Probability Spectrum")
            ax.set_xlabel("Neutron Energy")
            ax.set_ylabel("Probability")
            ax.grid()

            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            ngraph = base64.b64encode(buf.getvalue()).decode()

            return render_template('calc/calc.html', xsect = xsects,nspec = nspec,ngraph=ngraph,alphas_list = alphas, mat_list = mat)
        
    else:
        return render_template('calc/calc.html')
