import ckan.plugins.toolkit as toolkit


class DataPackagerHomeController(toolkit.BaseController):

    def api(self):

        return toolkit.render('home/api.html')
