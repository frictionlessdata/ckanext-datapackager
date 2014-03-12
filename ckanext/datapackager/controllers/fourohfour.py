import ckan.plugins.toolkit as toolkit


class DataPackager404Controller(toolkit.BaseController):

    def fourohfour(self):

        toolkit.abort(404)
