import os
import time
import json
import datetime
from carpool.models import Match, AppParamsTeam

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

EVENTS_JSON_PATH = os.path.join(SCRIPT_DIR, "events.json")


class MatchObj(object):
    def __init__(self, match, app_param, end_time):
        self.match = match
        self.app_param = app_param
        self.end_time = end_time

    def __repr__(self):
        return "<MatchObj match: %r, app: %r, end time: %r" % (self.match, self.app_param, self.end_time)


def main():
    matches_data = []
    time_of_earliest_matches_to_get = (datetime.datetime.now() - datetime.timedelta(days=90)).date()
    upcoming_matches = Match.objects.filter(date__gte=time_of_earliest_matches_to_get).order_by("date")

    last_date = upcoming_matches.first().date
    current_date = last_date
    matches_on_last_date = {}
    matches_on_current_date = {}

    for match in upcoming_matches:
        if match.date - current_date >= datetime.timedelta(days=1):
            last_date = current_date
            if match.date - current_date >= datetime.timedelta(days=2):
                # If we are already 2 days after the last saved date, start
                # fresh (there are no previous matches that will continue to
                # the current date)
                matches_on_last_date = {}
            else:
                # We are 1 day later than the previous match's date, so if a
                # match from the previous day will repeat itself we will unify
                # them
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
            # This match is a continuation of a match from the previous day
            match_obj = matches_on_last_date[match.title]
            match_obj.end_time = current_date + datetime.timedelta(days=1)
            matches_on_current_date[match.title] = match_obj
        else:
            match_obj = MatchObj(
                match=match,
                app_param=app_param,
                end_time=None
            )
            matches_data.append(match_obj)
            matches_on_current_date[match.title] = match_obj

    # Transform match objects to event format
    events_data = []
    for match_obj in matches_data:
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

        events_data.append({
            "title": title,
            "start": start_time,
            "end": end_time,
            "url": url,
        })

    result = {}
    result["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    result["events"] = events_data

    #print(json.dumps(result))
    open(EVENTS_JSON_PATH, "wb").write(json.dumps(result))
    print("Updated %s" % EVENTS_JSON_PATH)


if __name__ == '__main__':
    main()
