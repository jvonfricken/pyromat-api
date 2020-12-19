from flask import Flask
from flask import jsonify
import numpy as np
import pyromat as pm
from flask import request
from flask_cors import CORS, cross_origin
from flask.logging import create_logger

app = Flask(__name__)
LOG = create_logger(app)
CORS(app, support_credentials=True)


@app.before_request
def log_request_info():
    LOG.debug('Headers: %s', request.headers)
    LOG.debug('Body: %s', request.get_data())


@app.route('/sat', methods=['POST'])
def hello_world():

    body = request.get_json()

    units = body['units']

    set_units(units)

    selected_species = pm.get(body['species'])

    chart_data = build_chart_data(selected_species)

    if 'pressure' in body:
        pressure_float = float(body['pressure'])
        return jsonify({
            "values": build_saturation_response_from_pressure(selected_species, pressure_float),
            "chart_data": chart_data
        })

    if 'temp' in body:
        temp_float = float(body['temp'])
        return jsonify({
            "values": build_saturation_response_from_temp(selected_species, temp_float),
            "chart_data": chart_data
        })


def build_saturation_response_from_pressure(selected_species, pressure):
    temp = selected_species.Ts(p=pressure)
    e_fluid, e_gas = selected_species.es(p=pressure)
    h_fluid, h_gas = selected_species.hs(p=pressure)
    s_fluid, s_gas = selected_species.ss(p=pressure)
    d_fluid, d_gas = selected_species.ds(p=pressure)
    v_fluid = 1/d_fluid
    v_gas = 1/d_gas

    selected_species_gas = {
        'phase': 'gas',
        'e': e_gas[0],
        'h': h_gas[0],
        's': s_gas[0],
        'v': v_gas[0],
        't': temp[0],
        'p': pressure
    }

    selected_species_liquid = {
        'phase': 'fluid',
        'e': e_fluid[0],
        'h': h_fluid[0],
        's': s_fluid[0],
        'v': v_fluid[0],
        't': temp[0],
        'p': pressure
    }

    return [selected_species_gas, selected_species_liquid]


def build_saturation_response_from_temp(selected_species, temp):
    p = selected_species.ps(T=temp)
    e_fluid, e_gas = selected_species.es(T=temp)
    h_fluid, h_gas = selected_species.hs(T=temp)
    s_fluid, s_gas = selected_species.ss(T=temp)
    d_fluid, d_gas = selected_species.ds(T=temp)
    v_fluid = 1/d_fluid
    v_gas = 1/d_gas

    selected_species_gas = {
        'phase': 'gas',
        'e': e_gas[0],
        'h': h_gas[0],
        's': s_gas[0],
        'v': v_gas[0],
        't': temp,
        'p': p
    }

    selected_species_liquid = {
        'phase': 'fluid',
        'e': e_fluid[0],
        'h': h_fluid[0],
        's': s_fluid[0],
        'v': v_fluid[0],
        't': temp,
        'p': p
    }

    return [selected_species_gas, selected_species_liquid]


def set_units(units):
    pm.config['unit_temperature'] = units['uT']
    pm.config['unit_pressure'] = units['up']
    pm.config['unit_matter'] = units['uM']
    pm.config['unit_energy'] = units['uE']
    pm.config['unit_volume'] = units['uV']


def build_chart_data(species):
    Tt = species.triple()[0]
    Tc = species.critical()[0]
    temp = (Tc - Tt) * .00001
    T = np.linspace(Tt+temp, Tc-temp, 100)
    sat_liquid, sat_vapor = species.ss(T)
    return {
        'temp_values': T.tolist(),
        'sat_liquid': sat_liquid.tolist(),
        'sat_vapor': sat_vapor.tolist()
    }
