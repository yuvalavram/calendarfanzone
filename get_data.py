import json
import datetime
from carpool.models import Match, AppParamsTeam


class MatchObj(object):
    def __init__(self, match, app_param, end_time):
        self.match = match
        self.app_param = app_param
        self.end_time = end_time


def main():
    matchs_data = []
    time_of_earliest_matches_to_get = (datetime.datetime.now() - datetime.timedelta(days=90)).date()
    upcoming_matches = Match.objects.filter(date__gte=time_of_earliest_matches_to_get).order_by("date")

    # Choose arbitrary dates in the past
    last_date = datetime.date(2000, 1, 1)
    current_date = datetime.date(2000, 1, 1)
    matches_on_last_date = {}
    matches_on_current_date = {}

#    for match in upcoming_matches:
#        # If we are already 2 days after the last saved date, switch it to the
#        # current date (which should now be "yesterday")
#        if match.date - last_date > datetime.timedelta(days=1):
#            last_date = current_date
#            matches_on_last_date = matches_on_current_date
#
#            current_date = match.date
#            matches_on_current_date = {}
#
#        app_param = None
#        url = ""
#        try:
#            # TODO: Don't choose first app params but use some other way to decide which app params to take
#            app_param = AppParamsTeam.objects.filter(team=match.home_team).first().app_params
#            url = app_param.meta_data["og_url"]
#        except:
#            print("Failed to find url for match id %s" % (match.id))
#            pass
#
#        if match.title in matches_on_last_date:
#            match_obj = matches_on_last_date[match.title]
#            match_obj["end"] = current_date + datetime.timedelta(days=1)
#            matches_on_current_date[match.title] = match_obj
#        else:
#            match_obj = {
#                #"match_id": match.id,
#                "title": "%s: %s" % (app_param.app_name, match.title) if app_param is not None else match.title,
#                "start": match.date, #.strftime("%Y-%m-%d"),
#                "end": 0, # match.strftime("%Y-%m-%d"),
#                "url": app_param.meta_data["og_url"] if app_param is not None else "",
#            }
#            matchs_data.append(match_obj)
#            matches_on_current_date[match.title] = match_obj

    for match in upcoming_matches:
        # If we are already 2 days after the last saved date, switch it to the
        # current date (which should now be "yesterday")
        if match.date - last_date > datetime.timedelta(days=1):
            last_date = current_date
            matches_on_last_date = matches_on_current_date

            current_date = match.date
            matches_on_current_date = {}

        app_param = None
        try:
            # TODO: Don't choose first app params but use some other way to decide which app params to take
            app_param = AppParamsTeam.objects.filter(team=match.home_team).first().app_params
        except:
            print("Failed to find app param for match id %s" % (match.id))

        if match.title in matches_on_last_date:
            match_obj = matches_on_last_date[match.title]
            match_obj.end = current_date + datetime.timedelta(days=1)
            matches_on_current_date[match.title] = match_obj
        else:
            match_obj = MatchObj(
                match=match,
                app_param=app_param,
                end_time=None
            )
            matchs_data.append(match_obj)
            matches_on_current_date[match.title] = match_obj

    # Transform match objects to event format
    result = []
    for match_obj in matchs_data:
        title = match_obj.match.title
        url = ""
        if match_obj.app_param:
            app_param_name = match_obj.app_param.app_name
            # Specifically shorten live park...
            if (app_param_name == "Live Park Events"):
                app_param_name = "Livepark"
            title = "%s: %s" % (app_param_name, match_obj.match.title)
            url = "%s/#/event/%s" % (match_obj.app_param.meta_data["og_url"], match_obj.match.id)

        start_time = match_obj.match.date.strftime("%Y-%m-%d")
        end_time = 0
        if match_obj.end_time:
            end_time = match_obj.end_time.strftime("%Y-%m-%d")

        result.append({
            "title": title,
            "start": start_time,
            "end": end_time,
            "url": url,
        })

    print(json.dumps(result))


if __name__ == '__main__':
    main()
