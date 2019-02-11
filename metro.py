import requests


class Connection:
    API = 'http://api.metro.net/agencies/lametro/'
    """
    Using the base URL, all requests will be passed through here and return
    in JSON format
    """

    def _request(self, command):
        """
        HTTP request to the API and return a specific result based on command
        """
        url = self.API + command
        r = requests.get(url)
        return r.json()


class Routes(Connection):

    def routes(self):
        """
        Get the list of all Metro's routes
        """
        return self._request('routes/')

    def route_info(self, bus_number: int):
        """
        Get info for specified route element
        """
        return self._request(f'routes/{bus_number}')

    def stop_locations(self, bus_number: int):
        """
        Get the collection of stops for specified route/bus number
        """
        return self._request(f'routes/{bus_number}/stops/')['items']

    def arrival_predictions(self, bus_number: int, stop_number: int):
        """
        Get bus arrival predictions for stop number on route/bus number
        """
        return self._request(f'routes/{bus_number}/stops/{stop_number}/predictions/')

    def stop_sequence(self, bus_number: int):
        """
        Get stop sequence for specified route
        """
        return self._request(f'routes/{bus_number}/sequence/')

    def vehicle_run(self, bus_number: int):
        """
        Get runs of specified route/bus number; which way the bus is headed
        """
        return self._request(f'routes/{bus_number}/runs/')['items']


class Stops(Connection):

    def all_arrival_predictions(self, stop_number: int):
        """
        Get bus arrival predictions for all routes serving specified stop
        """
        return self._request(f'stops/{stop_number}/predictions/')['items']


class Vehicles(Connection):

    def all_vehicles(self):
        """
        Get the current geolocation for all Metro's vehicle positions
        """
        self._request('vehicles/')

    def vehicle_list(self, bus_number: int):
        """
        Get the list of vehicles currently running on specified route/bus number
        """
        return self._request(f'routes/{bus_number}/vehicles/')
