import ckan.plugins.toolkit as toolkit


class B2404Controller(toolkit.BaseController):

    def fourohfour(self):

        toolkit.abort(404)
