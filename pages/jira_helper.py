# -*- coding: utf-8 -*-

# Why jira API is slow, check out:
# https://jira.atlassian.com/browse/JRA-36224
# https://jira.atlassian.com/browse/JRA-30170
from collections import defaultdict
from DateTime import DateTime

from jira.client import JIRA
import config

__author__ = 'kevin.cai'

class JiraHelper(object):

    class StoryPriorityType:
        Major = "Major"
        Blocker = "Blocker"
        Critical = "Critical"
        Minor = "Minor"
        Trivial = "Trivial"
        Low = "Low"

    class BugStatus:
        open = "OPEN"
        in_progress = "IN PROGRESS"
        resolved = "RESOLVED"
        reopened = "REOPENED"
        closed = "CLOSED"

    class IssueType:
        StandardType = "standardIssueTypes()"
        Bug = "bug"
        Story = "Story"
        LiveDefect = '"Live Defect"'
        ChangeRequest = '"Change Request"'
        Defect = Bug + "," + LiveDefect

    class Label:
        auto = "AUTO"

    class TimeZone:
        Eastern = "US/Eastern"
        UTC = "UTC"
        China = "Asia/Shanghai"

    def __init__(self, jira_server, securityUser=None):
        if securityUser:
            try:
                self.jira = JIRA(options = jira_server, basic_auth=(securityUser['username'], securityUser['password']))
            except Exception,e:
                self.jira = None
        else:
            try:
                self.jira =JIRA(options = jira_server)
            except Exception,e:
                self.jira = None

    def get_num_of_sprint_names_by_board_id(self, id_of_board, num=config.num_of_sprint_shown):
        '''
        return previous [number] of the sprint names that belong to given board id.
        [number] = num_of_sprint_shown + 1
        :param id_of_board:
        :return:
        '''
        sp_list = []
        sp_name = []
        sp = self.jira.sprints(id_of_board)
        active_sprint_id = None
        for s in sp:
            sp_list.append(s.raw['id'])

            if s.raw["state"] == "ACTIVE":
                active_sprint_id = s.raw['id']

        current_index = sorted(sp_list).index(active_sprint_id)

        target_sprint_list = sorted(sp_list)[current_index-num-1:current_index +1]

        for s in sp:
            if s.raw['id'] in target_sprint_list:
                sp_name.append((str(s.raw['name']), str(s.raw['name'])))

        return sp_name

    def get_active_sprint_id_by_board_id(self, id_of_board):
        return_list = []
        sp = self.jira.sprints(id_of_board)
        for i in sp:
            if i.raw["state"] == "ACTIVE":
               return_list.append(i.raw['id'])

        return return_list

    def get_sprint_id_by_sprint_name(self, id_of_board, sprint_name):

        sp = self.jira.sprints(id_of_board)
        sprint_name = (str(sprint_name).strip()).lower()
        for item in sp:
            if unicode(item).encode('utf-8').strip().lower() == sprint_name:
                return int(item.raw['id'])

    def get_fix_version_by_sprint_id(self, sprint_id):
        '''
        this function may be not accurate, can a sprint have more than one fixversion?
        :param sprint_id:
        :return:
        '''
        story_ids = self.get_story_id_by_sprint(sprint_id)
        for s in story_ids:
            if hasattr(s.fields, "fixVersions"):
                if s.fields.fixVersions:
                    return str(s.fields.fixVersions[0])

    def get_sprint_info(self, sprint_id, id_of_board):
        '''

        :param sprint_id:
        :param id_of_board:
        :return:
        {
            u'startDate': u'07/Dec/15 10:00 AM',
             u'endDate': u'25/Dec/15 6:00 PM',
             u'name': u'Sprint 1516 (12/07 - 12/25)',
             u'remoteLinks': [],
             u'sequence': 1810,
             u'completeDate': u'28/Dec/15 11:58 AM',
             u'state': u'CLOSED',
             u'linkedPagesCount': 0,
             u'daysRemaining': 0,
             u'id': 1842
        }

        '''
        return self.jira.sprint_info(id_of_board, sprint_id)

    def get_return_value_from_api_request(self, restful_string, property):
        return self.jira.find(restful_string, property).raw["issues"]

    def get_actual_story_points_by_sprint(self, standard_tasks_info_by_sprint):
        story_point = 0
        for i in standard_tasks_info_by_sprint:
            if i["Story_point"]:
                story_point += int(i["Story_point"])
        return story_point

    def get_issue_closed_date_by_id(self, id):
        issue = self.jira.issue(id, expand='changelog')
        change_log = issue.changelog
        closed_date = None
        for history in change_log.histories:
            for item in history.items:
                if item.field == 'status':
                    if item.toString == 'Closed':
                        closed_date = history.created
                        # closed_date = self.convert_time_zone(history.created)
        if issue.fields.status == 'Closed':
            return closed_date
        else:
            return None

    def get_issue_closed_status_by_date(self, id, date):
        issue = self.jira.issue(id, expand='changelog')
        change_log = issue.changelog
        closed_date = None
        for history in change_log.histories:
            for item in history.items:
                if item.field == 'status':
                    if item.toString == 'Closed':
                        closed_date = history.created

        if closed_date:
            if DateTime(closed_date) > DateTime(date):
                return None
        return closed_date

    def get_issue_resolved_status_by_date(self, id, date):
        '''
            If issue closed date < = date, then resolved return None.
        '''
        issue = self.jira.issue(id, expand='changelog')
        change_log = issue.changelog
        resolved_date = None
        for history in change_log.histories:
            for item in history.items:
                if item.field == 'status':
                    if item.toString == 'Resolved':
                        resolved_date = history.created

        if resolved_date:
            if DateTime(resolved_date) > DateTime(date):
                return None

            closed_date = self.get_issue_closed_status_by_date(id, date)
            if closed_date:
                    return None

        return resolved_date


    def get_issue_resoved_date_by_id(self, id):
        issue = self.jira.issue(id, expand='changelog')
        change_log = issue.changelog
        resolved_date = None
        for history in change_log.histories:
            for item in history.items:
                if item.field == 'status':
                    if item.toString == 'Resolved':
                        resolved_date = history.created

        if issue.fields.status == 'Closed':
            return resolved_date
        else:
            return None

    def get_task_status_change_date(self, id):
        '''
        :param id:
        :return:  [('2016-01-13', 'Created'), ('2016-01-14', 'Created'), ('2016-01-15', 'Created'), ('2016-01-16', 'Created'), ('2016-01-17', 'Created'), ('2016-01-18', 'Created'), ('2016-01-19', 'Created'), ('2016-01-20', 'Created'), ('2016-01-21', 'Created'), ('2016-01-22', 'Created'), ('2016-01-23', 'Created'), ('2016-01-24', 'Created'), ('2016-01-25', 'Created'), ('2016-01-26', 'Created'), ('2016-01-27', 'Created'), ('2016-01-28', 'Created'), ('2016-01-29', 'Created'), ('2016-01-30', 'Created'), ('2016-01-31', 'Created'), ('2016-02-01', 'Created'), ('2016-02-02', 'Created'), ('2016-02-03', 'Created'), ('2016-02-04', 'Created')]

        '''
        return_dict = {}
        temp_dict = {}
        raw_status_change_dict = {}
        issue = self.jira.issue(id, expand='changelog')
        change_log = issue.changelog
        for history in change_log.histories:
            for item in history.items:
                if item.field == 'status':
                    if item.toString == 'Resolved':
                        raw_status_change_dict[DateTime(history.created)] = "Resolved"
                    if item.toString == 'Closed':
                        raw_status_change_dict[DateTime(history.created)] = "Closed"
                    if item.toString == 'Reopened':
                        raw_status_change_dict[DateTime(history.created)] = "Open"
        # raw_status_change_dict[DateTime(issue.fields.created)] = "Created"

        ## Get the sorted date with status.
        for k in raw_status_change_dict.keys():
            str_k = str(k.asdatetime().strftime("%Y-%m-%d"))
            if str_k not in temp_dict.keys():
                return_dict[str_k] = raw_status_change_dict[k]
                temp_dict[str_k] = k
            else:
                if k > temp_dict[str_k]:
                    return_dict[str_k] = raw_status_change_dict[k]
                else:
                    return_dict[str_k] = raw_status_change_dict[temp_dict[str_k]]

        return_dict[DateTime(issue.fields.created).asdatetime().strftime("%Y-%m-%d")] = "Created"
        # return_dict["id"] = id
        return_list= sorted(return_dict.iteritems(), key=lambda d:d[0])

        #Get the sorted status till end of call day.
        final_dict = {}
        i=0
        if len(return_list) > 1:
            while i < len(return_list)-1:
                start =  DateTime(str(return_list[i][0]))
                end = DateTime(str(return_list[i+1][0]))
                while start <= end:
                    final_dict[start.asdatetime().strftime("%Y-%m-%d")] = return_list[i][1]
                    start +=1
                i +=1
        else:
            final_dict[return_list[0][0]] = return_list[0][1]
        return final_dict #sorted(final_dict.iteritems(), key=lambda d:d[0]) #


    def get_closed_task_num_group_by_date(self, j_query):
        '''
        return the  date number pair with given jquery.
        :param : project = 'ATEAM' AND issuetype = bug and created >= {start_day} AND created <= {end_day} and sprint={}
        :return: return nested list [['2015-12-20', 5],['2015-12-30', 2]]
        '''
        issue_ids = self.get_task_id_by_query_string(j_query)

        key_date_dict = {}
        date_key_dict = {}
        target_list = []
        for item in issue_ids:
            closed_date = self.get_issue_closed_date_by_id(str(item))
            if closed_date:
                key_date_dict[item] = closed_date
        for k, v in key_date_dict.iteritems():
            date_key_dict.setdefault(v, []).append(k)

        for k, v in date_key_dict.items():
            temp_list = []
            temp_list.append(k)
            temp_list.append(len(v))
            target_list.append(temp_list)
        return  sorted(target_list)

    def get_total_bug_and_closed_open_bug_num_by_time_period(self, j_query, end_day):
        '''
         Get the total , closed and still opened pair before end day.
        :param j_query: eg:
        "project = {project} AND issuetype in ({issue_type}) and created >= {start_day} AND created <= {end_day}

        :param
        end_day: DATETIME format. DateTime(end_time)
        :return:


        '''
        issue_ids = self.get_task_id_by_query_string(j_query)
        closed_number = 0
        resoved_number = 0
        for item in issue_ids:
            closed_date = self.get_issue_closed_status_by_date(str(item), end_day)
            resolved_date = self.get_issue_resolved_status_by_date(str(item), end_day)
            if closed_date:
                if DateTime(closed_date).asdatetime().strftime("%Y-%m-%d") <= DateTime(end_day).asdatetime().strftime("%Y-%m-%d"):
                    closed_number +=1
            if resolved_date:
                if DateTime(resolved_date).asdatetime().strftime("%Y-%m-%d") <= DateTime(end_day).asdatetime().strftime("%Y-%m-%d"):
                    resoved_number +=1

        return len(issue_ids), len(issue_ids) - closed_number, closed_number, resoved_number, len(issue_ids) - closed_number - resoved_number

    # def html_get_total_bug_and_open_bug_trend_by_sprint(self, sprint_id, id_of_board=config.board_id, project=config.project_name, component_filter=None):
    #     '''
    #     :param id_of_board:
    #     :param sprint_id:
    #     :return: [
    #       ['Date',  'total bug number', 'Opened bug number'],
    #       ['2015-12-07', 0, 0], ['2015-12-08', 0, 0], ['2015-12-09', 0, 1], ['2015-12-10', 2, 3], ['2015-12-11', 3, 5], ['2015-12-12', 4, 6]
    #       ]
    #     '''
    #     # Version1 and Version2, bug trends should use this block.
    #         # sprint_info = self.get_sprint_info(sprint_id, id_of_board)
    #         #
    #         # start_date = DateTime(sprint_info["startDate"])
    #         # end_date = DateTime(sprint_info["endDate"])
    #         # current_date = DateTime(start_date)
    #         # nested_list_for_html = []
    #         # title_list = ["date", "total bug number", "opened bug number"]
    #         # nested_list_for_html.append(title_list)
    #         #
    #         # while current_date <= end_date:
    #         #     j_query_string = '''project = {project} AND issuetype in ({issue_type}) and created >= {start_day} AND created <= {end_day}'''\
    #         #         .format(project= project, issue_type= self.IssueType.Bug, start_day=start_date.asdatetime().strftime("%Y-%m-%d"), end_day=current_date.asdatetime().strftime("%Y-%m-%d"))
    #         #     temp_list = []
    #         #     temp_list.append(current_date.asdatetime().strftime("%Y-%m-%d"))
    #         #
    #         #     bug_number_info = self.get_total_bug_and_open_bug_num_by_time_period(j_query_string, current_date)
    #         #     total_number = bug_number_info[0]
    #         #     opened_number = bug_number_info[1]
    #         #     temp_list.append(total_number)
    #         #     temp_list.append(opened_number)
    #         #     nested_list_for_html.append(temp_list)
    #         #     current_date = current_date +1
    #         #
    #         # return nested_list_for_html
    #
    #     # Version 3, current use
    #     sprint_info = self.get_sprint_info(sprint_id, id_of_board)
    #     start_date = DateTime(sprint_info["startDate"])
    #     end_date = DateTime(sprint_info["endDate"])
    #     current_date = DateTime(start_date)
    #     nested_list_for_html = []
    #     title_list = ["date", "closed bugs", "resolved bugs", "open bugs"]
    #     nested_list_for_html.append(title_list)
    #
    #     while current_date <= end_date:
    #         j_query_string = '''project = {project} AND issuetype in ({issue_type}) and created >= {start_day} AND created <= {end_day}'''\
    #             .format(project= project, issue_type= self.IssueType.Bug, start_day=start_date.asdatetime().strftime("%Y-%m-%d"), end_day=current_date.asdatetime().strftime("%Y-%m-%d"))
    #         temp_list = []
    #         temp_list.append(current_date.asdatetime().strftime("%Y-%m-%d"))
    #
    #         if component_filter:
    #             j_query_string = j_query_string + ''' and component in ({component})'''.format(component=component_filter)
    #         bug_number_info = self.get_total_bug_and_closed_open_bug_num_by_time_period(j_query_string, current_date)
    #         closed_number = bug_number_info[2]
    #         resolved_number = bug_number_info[3]
    #         opened_number = bug_number_info[4]
    #         temp_list.append(closed_number)
    #         temp_list.append(resolved_number)
    #         temp_list.append(opened_number)
    #         nested_list_for_html.append(temp_list)
    #         current_date = current_date +1
    #
    #     return nested_list_for_html

    def html_get_total_bug_and_open_bug_trend_by_sprint(self, sprint_id, id_of_board=config.board_id, project=config.project_name, component_filter=None):
        '''
        :param id_of_board:
        :param sprint_id:
        :return: [
          ["date", "closed bugs", "resolved bugs", "open bugs"],
          ['2015-12-07', 0, 0, 0], ['2015-12-08', 0, 0, 0], ['2015-12-09', 0, 1, 1]
          ]
        '''
        sprint_info = self.get_sprint_info(sprint_id, id_of_board)
        start_date = DateTime(str(sprint_info["startDate"]) + ' ' +  "US/Eastern")
        end_date = DateTime(str(sprint_info["endDate"]) + ' ' +  "US/Eastern")

        nested_list_for_html = []
        title_list = ["date", "closed bugs", "resolved bugs", "open bugs"]
        nested_list_for_html.append(title_list)

        j_query_string = '''project = {project} AND issuetype in ({issue_type}) and created >= {start_day} AND created <= {end_day}'''\
                .format(project= project, issue_type= self.IssueType.Bug, start_day=start_date.asdatetime().strftime("%Y-%m-%d"), end_day=end_date.asdatetime().strftime("%Y-%m-%d"))

        if component_filter:
            j_query_string = j_query_string + ''' and component in ({component})'''.format(component=component_filter)

        all_ids = self.get_task_id_by_query_string(j_query_string)
        task_status_change_date_list = []
        for id in all_ids:
            data_status = self.get_task_status_change_date(str(id))

            sorted_data = sorted(data_status.iteritems(), key=lambda d:d[0])

            time_start = start_date
            while time_start <= end_date:
                str_start_date = time_start.asdatetime().strftime("%Y-%m-%d")
                if len(data_status) >=1:
                    if DateTime(str_start_date) < DateTime(sorted_data[0][0]):
                        data_status[str_start_date] = "NotOpen"

                    if DateTime(str_start_date) > DateTime(sorted_data[len(sorted_data)-1][0]):
                        data_status[str_start_date] = sorted_data[len(sorted_data)-1][1]

                time_start = DateTime(str_start_date)
                time_start  = time_start +1

            for k in data_status.keys():
                if DateTime(k) > DateTime(end_date.asdatetime().strftime("%Y-%m-%d")):
                    del data_status[k]

            task_status_change_date_list.append(data_status)

        status_dict = {}
        for d in task_status_change_date_list:
            for k, v in d.iteritems():
                status_dict.setdefault(k, []).append(v)

        for item in  sorted(status_dict.iteritems(), key=lambda d:d[0]):
            single_list = []
            single_list.append(item[0])
            single_list.append(item[1].count("Closed"))
            single_list.append(item[1].count("Resolved"))
            single_list.append(item[1].count("Created") + item[1].count("Open"))
            nested_list_for_html.append(single_list)

        return nested_list_for_html

    def get_task_info_by_id(self, id):
        issue = self.jira.issue(id)
        issue_dict = {}
        issue_dict["Key"] = issue.key
        issue_dict["Id"] = issue.id
        issue_dict["Summary"] = issue.fields.summary
        issue_dict["Priority"] = issue.fields.priority.name
        issue_dict["Status"] = issue.fields.status.name
        issue_dict["Created"] = issue.fields.created
        issue_dict["Story_point"] = issue.fields.customfield_10002
        issue_dict["Components"] = issue.fields.components
        return issue_dict

    def get_filtered_task_info_by_component(self, task_lists, component_value):
        return_list = []
        for l in task_lists:
            if l['Components']:
                if str(component_value) in str(l['Components']):
                    return_list.append(l)
        return return_list

    def get_filtered_task_id_by_component(self, task_id_lists, component_value):
        return_list = []
        for l in task_id_lists:
            item = self.get_task_info_by_id(l)
            if item.has_key("Components"):
                if str(component_value) in str(item['Components']):
                    return_list.append(l)
        return return_list


    def get_task_info_by_query_string(self, j_query):
        all_ids = self.jira.search_issues(j_query, maxResults=False)
        task_info = []
        for id in all_ids:
            task_info.append(self.get_task_info_by_id(id))
        return task_info

    def get_task_id_by_query_string(self, j_query):
        issue_list = []
        for item in self.jira.search_issues(j_query, maxResults=False):
            issue_list.append(str(item))
        return issue_list

    def get_automation_found_bug_info_by_sprint(self, sprint_id, id_of_board_id=config.board_id, project=config.project_name):
        '''
        All the automation bug will be marked with label AUTO
        :param sprint_id:
        :return:
        '''
        start_day = self.get_sprint_start_end_day(sprint_id, id_of_board_id)["start_day"]
        end_day = self.get_sprint_start_end_day(sprint_id, id_of_board_id)["end_day"]
        bug_query_string = '''project = "{project}" AND issuetype in ({issue_type}) and labels = "{label}" and created >="{start_day}" and  created <="{end_day}" '''.format(project=project, issue_type=self.IssueType.Defect, label=self.Label.auto, start_day=start_day, end_day=end_day)
        return self.get_task_info_by_query_string(bug_query_string)

    def get_automation_found_bug_id_by_sprint(self, sprint_id, id_of_board_id=config.board_id, project=config.project_name):
        start_day = self.get_sprint_start_end_day(sprint_id, id_of_board_id)["start_day"]
        end_day = self.get_sprint_start_end_day(sprint_id, id_of_board_id)["end_day"]
        bug_query_string = '''project = "{project}" AND issuetype in ({issue_type}) and labels = "{label}" and created >="{start_day}" and  created <="{end_day}" '''.format(project=project, issue_type=self.IssueType.Defect, label=self.Label.auto, start_day=start_day, end_day=end_day)
        return self.get_task_id_by_query_string(bug_query_string)

    def get_sprint_start_end_day(self, sprint_id, id_of_board_id=config.board_id):
        '''
        if sprint is still active, end_day is planned end day.
        :param sprint_id:
        :return:
        '''
        result_dict = {}
        sprint_info = self.get_sprint_info(sprint_id, id_of_board_id)

        result_dict["start_day"] = DateTime(sprint_info["startDate"]).asdatetime().strftime("%Y-%m-%d")
        if str(sprint_info["completeDate"]) != "None":
            result_dict["end_day"] = DateTime(sprint_info["completeDate"]).asdatetime().strftime("%Y-%m-%d")
        else:
            result_dict["end_day"] = DateTime(sprint_info["endDate"]).asdatetime().strftime("%Y-%m-%d")

        return result_dict

    def get_bug_info_by_sprint(self, sprint_id, id_of_board_id=config.board_id,  project=config.project_name):
        '''
        sprint completed will replaced by due date if sprint bis currently active.
        :param sprint_id:
        :return:
        '''
        start_day = self.get_sprint_start_end_day(sprint_id, id_of_board_id)["start_day"]
        end_day = self.get_sprint_start_end_day(sprint_id, id_of_board_id)["end_day"]
        bug_query_string = '''project = "{project}" AND issuetype in ({issue_type}) and created >="{start_day}" and  created <="{end_day}" '''.format(project=project, issue_type=self.IssueType.Bug, start_day=start_day, end_day=end_day)
        return self.get_task_info_by_query_string(bug_query_string)

    def get_bug_id_by_sprint(self, sprint_id, id_of_board_id=config.board_id, project=config.project_name):
        start_day = self.get_sprint_start_end_day(sprint_id, id_of_board_id)["start_day"]
        end_day = self.get_sprint_start_end_day(sprint_id, id_of_board_id)["end_day"]
        bug_query_string = '''project = "{project}" AND issuetype in ({issue_type}) and created >="{start_day}" and  created <="{end_day}" '''.format(project=project, issue_type=self.IssueType.Bug, start_day=start_day, end_day=end_day)
        return self.get_task_id_by_query_string(bug_query_string)

    def get_live_defect_info_by_sprint(self, sprint_id, project=config.project_name):
        live_defect_query_string = '''project = "{project}" AND issuetype in ({issue_type}) and sprint in ({sprint})'''.format(project=project, issue_type=self.IssueType.LiveDefect, sprint=sprint_id)
        return self.get_task_info_by_query_string(live_defect_query_string)

    def get_live_defect_id_by_sprint(self, sprint_id, project=config.project_name):
        live_defect_query_string = '''project = "{project}" AND issuetype in ({issue_type}) and sprint in ({sprint})'''.format(project=project, issue_type=self.IssueType.LiveDefect, sprint=sprint_id)
        return self.get_task_id_by_query_string(live_defect_query_string)

    def get_change_request_info_by_sprint(self, sprint_id, project=config.project_name):
        change_request_query_string = '''project = "{project}" AND issuetype in ({issue_type}) and sprint in ({sprint})'''.format(project=project, issue_type=self.IssueType.ChangeRequest, sprint=sprint_id)
        return self.get_task_info_by_query_string(change_request_query_string)

    def get_change_request_id_by_sprint(self, sprint_id, project=config.project_name):
        change_request_query_string = '''project = "{project}" AND issuetype in ({issue_type}) and sprint in ({sprint})'''.format(project=project, issue_type=self.IssueType.ChangeRequest, sprint=sprint_id)
        return self.get_task_id_by_query_string(change_request_query_string)

    def get_standard_tasks_info_by_sprint(self, sprint_id, project=config.project_name):
        standard_type_query = '''project = "{project}" AND issuetype in ({issue_type}) and sprint in ({sprint})'''.format(project=project, issue_type=self.IssueType.StandardType, sprint=sprint_id)
        return self.get_task_info_by_query_string(standard_type_query)

    def get_standard_tasks_id_by_sprint(self, sprint_id, project=config.project_name):
        standard_type_query = '''project = "{project}" AND issuetype in ({issue_type}) and sprint in ({sprint})'''.format(project=project, issue_type=self.IssueType.StandardType, sprint=sprint_id)

        return self.get_task_id_by_query_string(standard_type_query)

    def get_story_info_by_sprint(self, sprint_id, project=config.project_name):
        story_type_query = '''project = "{project}" AND issuetype in ({issue_type}) and sprint in ({sprint})'''.format(project=project, issue_type=self.IssueType.Story, sprint=sprint_id)
        return self.get_task_info_by_query_string(story_type_query)

    def get_story_id_by_sprint(self, sprint_id, project=config.project_name):
        story_type_query = '''project = "{project}" AND issuetype in ({issue_type}) and sprint in ({sprint})'''.format(project=project, issue_type=self.IssueType.Story, sprint=sprint_id)
        return self.get_task_id_by_query_string(story_type_query)

    def get_tasks_removed_from_current_sprint(self, sprint_id, project=config.project_name):
        fixversion = self.get_fix_version_by_sprint_id(sprint_id)
        task_removed_query = '''project = "{project}" AND issuetype in ({issue_type}) and fixversion was in "{fixversion}" and fixversion !="{fixversion}"'''.format(project=project, issue_type=self.IssueType.StandardType, fixversion=fixversion)
        return self.get_task_info_by_query_string(task_removed_query)

    def get_bugs_not_found_in_sprint_but_closed_in_sprint(self, sprint_id, id_of_board_id=config.board_id, project=config.project_name, component_filter=None):
        start_day = self.get_sprint_start_end_day(sprint_id, id_of_board_id)["start_day"]
        end_day = self.get_sprint_start_end_day(sprint_id, id_of_board_id)["end_day"]
        bug_query_string = '''project = "{project}" AND issuetype in ({issue_type}) and created <"{start_day}" and  resolved>="{start_day}" and resolved <="{end_day}" and status = {status} '''.format(project=project, issue_type=self.IssueType.Bug, start_day=start_day, end_day=end_day, status=self.BugStatus.closed)
        return self.get_task_info_by_query_string(bug_query_string)

    def get_task_id_that_has_linked_task(self, bug_id__list_by_sprint):
        task_id = []
        for id in bug_id__list_by_sprint:
            if self.get_id_and_linked_id_dict(id):
                task_id.append(self.get_id_and_linked_id_dict(id)["id"])
        return task_id

    def get_task_info_that_has_linked_task(self, sprint_id, id_of_board_id=config.board_id, project=config.project_name):
        ids = self.get_task_id_that_has_linked_task(sprint_id, id_of_board_id, project)
        info_list = []
        for id in ids:
            info_list.append(self.get_task_info_by_id(id))
        return info_list

    def get_id_and_linked_id_dict(self, id):
        issue_dict = {}

        for item in self.jira.find("/search?jql=id={}",id).raw["issues"]:
            temp_list = []
            if item["fields"].has_key("issuelinks"):
                for i in item["fields"]["issuelinks"]:
                    if i.has_key("outwardIssue"):
                        temp_list.append(i["outwardIssue"]["key"])
                    if i.has_key("inwardIssue"):
                        temp_list.append(i["inwardIssue"]['key'])
                    issue_dict['id'] = id
                    issue_dict['linked_id'] = temp_list
        return issue_dict

    def get_id_and_linked_id_by_sprint(self, sprint_id, project=config.project_name):
        ids = self.get_standard_tasks_id_by_sprint(sprint_id, project)
        result_list = []
        for id in ids:
            if self.get_id_and_linked_id_dict(id):
                result_list.append(self.get_id_and_linked_id_dict(id))
        return result_list

    def get_linked_task_id_by_sprint(self, sprint_id, project=config.project_name):
        id_list = []
        for item in self.get_id_and_linked_id_by_sprint(sprint_id, project):
            id_list.append(item["linked_id"])
        return id_list

    def get_linked_task_info_by_id(self, id):
         id_linked_id_pair = self.get_id_and_linked_id_dict(id)
         result_list = []
         if id_linked_id_pair:
             for i in id_linked_id_pair["linked_id"]:
                 result_list.append(self.get_task_info_by_id(i))
         return result_list

    def get_linked_task_info_by_sprint(self, sprint_id, project=config.project_name):
        '''
        Return all the linked task detail info if the stories in given sprint has/have linked tasks.
        '''
        all_ids = self.get_linked_task_id_by_sprint(sprint_id, project)
        issue_list =[]
        for id in all_ids:
            for i in id:
                issue_list.append(self.get_task_info_by_id(i))
        return issue_list

    def html_get_bug_list_by_tasks(self, task_list):
        '''
        :param sprint_id:
        :return:
        eg: [
                ['bug_id-1', 'priority', 'summary', 'status'],
                ['bug_id-1', 'priority', 'summary', 'status']
            ]
        '''

        bug_list_for_html = []

        for dict in task_list:
            bug_info = []

            bug_info.append('''<a href="https://jira.englishtown.com/browse/{}">'''.format(dict["Key"]) + dict["Key"] + '''</a>''')
            bug_info.append(dict["Priority"])
            bug_info.append(dict["Summary"])
            bug_info.append(dict["Status"])
            bug_list_for_html.append(bug_info)

        str_nested_list = self.remove_duplicated_value(bug_list_for_html)

        return str(str_nested_list).replace("u", '')

    def html_get_linked_issue_list_by_tasks(self, task_list_has_linked_issue):
        '''

        :param task_list_has_linked_issue:
        :return: list
        '''
        return self.html_get_bug_list_by_tasks(task_list_has_linked_issue)

    def remove_duplicated_value(self, list):
        new_list = []
        for l in list:
            if l not in new_list:
                new_list.append(l)
        return new_list

    def html_get_share_ratio_by_priority(self, issue_list, category="Priority"):
        '''
        :param :
        :return:
            eg: [
            ['priority', 'number'],
            ['Blocker', 1],
            ['Major', 5],
            ['Critical', 1],
            ['Minor', 2]
            ]
        '''
        title="PriorityCategory"
        value="Numbers"
        issue_dict = self.get_issue_num_group_by_Category(issue_list, category)
        issue_dict[title] = value
        return self.convert_dict_to_str_list(issue_dict)

    def html_get_share_ratio_detail_by_priority(self, issue_list):
        '''

        :param :
        :return: eg:
        [['Blocker', ['ATEAM-3913']],
         ['Major', ['ATEAM-3922', 'ATEAM-3941'] ],
         ['Critical', ['ATEAM-3919']],
         ['Minor', ['ATEAM-3921', 'ATEAM-3920']]]

        '''
        issues = self.get_issue_key_group_by_priority(issue_list)
        return str(issues).replace("u", "")

    def get_issue_num_group_by_Category(self, bug_list, category):
        '''
        The category must be the item of the tasks, like  "Key", "Id", "Summary", "Priority", "Status", "Created", "Story_point"
        :param bug_list:
        :param category:
        :return:
        '''
        priority_num_dict = {}
        bug_priority_list = []

        for dict in bug_list:
            bug_priority_list.append((dict[category]))

        for i in bug_priority_list:
            if bug_priority_list.count(i)>0:
                priority_num_dict[i] = bug_priority_list.count(i)

        return priority_num_dict

    def get_linked_issue_detail_group_by_story(self, id_has_linked_id):
        '''

        :param id_has_linked_id: ef:
        [   <JIRA Issue: key=u'ATEAM-3941', id=u'186701'>,
            <JIRA Issue: key=u'ATEAM-3919', id=u'185391'>,
            <JIRA Issue: key=u'ATEAM-3913', id=u'185188'>
        ]
        :return:

        {
        u'ATEAM-3880': [<JIRA Issue: key=u'ATEAM-3922', id=u'185700'>],
        u'ATEAM-3884': [<JIRA Issue: key=u'ATEAM-3920', id=u'185414'>], u'ECS-4894': [<JIRA Issue: key=u'ATEAM-3941', id=u'186701'>],
         }
        '''

        story_list = []
        story_dict_with_linked_issue = {}
        for id in id_has_linked_id:
            for story in self.get_linked_task_info_by_id(id):
                temp_dict = {}
                temp_dict[story["Key"]] = id
                story_list.append(temp_dict)

        for item in story_list:
            for k, v in item.iteritems():
                story_dict_with_linked_issue.setdefault(k, []).append(v)

        return story_dict_with_linked_issue

    def html_get_linked_issue_detail_group_by_story(self, id_has_linked_id, bug_id_list_by_sprint):
        dict_result = self.get_linked_issue_detail_group_by_story(id_has_linked_id)
        str_format_result = {}
        story_related_issue_id = []

        no_story_related_issue = []

        for k in dict_result.iterkeys():
            str_list = []
            for i in dict_result[k]:
                str_list.append(str(i))
            str_format_result[k] = str_list
        story_related_issue_detail = str(str_format_result).replace("u", "")

        for k in str_format_result.keys():
            for v in str_format_result[k]:
                story_related_issue_id.append(v)

        for id in bug_id_list_by_sprint:
            if str(id) not in story_related_issue_id:
                no_story_related_issue.append(str(id))
        return story_related_issue_detail, no_story_related_issue

    def html_get_linked_issue_num_group_by_story(self, task_id_list_has_linked_task):
        '''

        :param task_id_list_has_linked_task:
        [   <JIRA Issue: key=u'ATEAM-3941', id=u'186701'>,
            <JIRA Issue: key=u'ATEAM-3919', id=u'185391'>,
            <JIRA Issue: key=u'ATEAM-3913', id=u'185188'>
        ]
        :return:
        [   ['Story', 'BugNum'], #this list must be the head list.
            [u'ATEAM-3880', 4],
            [u'ECS-4894', 1],
            [u'ATEAM-3884', 1]
        ]
        '''
        title="Story"
        value="BugNum"
        nested_lists = []
        title_list =[]

        title_list.append(title)
        title_list.append(value)
        nested_lists.append(title_list)

        story_dict_with_linked_issue = self.get_linked_issue_detail_group_by_story(task_id_list_has_linked_task)
        for item in story_dict_with_linked_issue:
            story_related_issue = []
            story_related_issue.append(item)
            story_related_issue.append(len(story_dict_with_linked_issue[item]))
            nested_lists.append(story_related_issue)

        return str(nested_lists).replace("u", "")

    def html_get_live_defect_percentage_of_all_defects(self, live_defect_id_list_by_sprint, bug_id__list_by_sprint):
        live_defect_num = len(live_defect_id_list_by_sprint)
        all_defect_num = len(bug_id__list_by_sprint) + live_defect_num

        return self.calculate_task_percentage(live_defect_num, all_defect_num)

    def html_get_change_request_percentage_of_all_defects(self, standard_tasks_id_list_by_sprint, change_request_id_list_by_sprint):
        all_tasks = len(standard_tasks_id_list_by_sprint)
        change_request = len(change_request_id_list_by_sprint)
        return self.calculate_task_percentage(change_request, all_tasks)

    def calculate_task_percentage(self, target_task_num, total_task_num):
        if int(total_task_num) == 0:
            return "N/A"
        else:
            percentage = float(target_task_num)/float(total_task_num)
            return format(percentage, '.2%')

    def html_get_automation_found_bug_percentange(self, bug_id_list_by_sprint, auto_found_bug_info_list):
        all_defect_num = len(bug_id_list_by_sprint)
        auto_bug = len(auto_found_bug_info_list)
        return self.calculate_task_percentage(auto_bug, all_defect_num)

    def get_issue_key_group_by_priority(self, bug_list):
        bug_dict = {}
        priority_key_dict = {}

        for dict in bug_list:
            bug_dict[(dict["Key"])] = (dict["Priority"])

        for k, v in bug_dict.iteritems():
            priority_key_dict.setdefault(v, []).append(k)

        return priority_key_dict

    def get_linked_issue_key_group_by_priority(self, bug_list):
        bug_dict = {}
        priority_key_dict = {}

        for dict in bug_list:
            bug_dict[(dict["linked_issue"]["Key"])] = (dict["linked_issue"]["Priority"])

        for k, v in bug_dict.iteritems():
            priority_key_dict.setdefault(v, []).append(k)

        return priority_key_dict

    def convert_dict_to_str_list(self, dict_to_convert):
        '''
        :param dict_to_convert: eg:
        {'PriorityCategory': 'Numbers', u'Blocker': 1, u'Major': 6, u'Critical': 1, u'Minor': 2}
        :return:
        [['PriorityCategory', 'Nmbers'], ['Blocker', 1], ['Major', 6], ['Critical', 1], ['Minor', 2]]
        '''
        str_list = []
        for k, v in dict_to_convert.iteritems():
            temp = [k, v]
            str_list.append(temp)

        return str(str_list).replace("u", "")

    def convert_time_zone(self, date_time , target_time_format=TimeZone.China):
        us_standard_time = DateTime(date_time)
        return DateTime(us_standard_time).toZone(target_time_format)

    def html_get_sprint_status(self, sprint_id, id_of_board=config.board_id):
        sprint_info = self.get_sprint_info(sprint_id, id_of_board)
        status = None
        if str(sprint_info["completeDate"]) != str(status):
            if DateTime(sprint_info["completeDate"]) < DateTime(sprint_info["endDate"]) + config.delay_day:
                status = "success"
            else:
                status = "fail"
        return status

if __name__ == "__main__":
    jira = JiraHelper(config.jira_options, config.jira_account)
    # print jira.get_task_info_by_id("ATEAM-4111")
    # print jira.get_task_status_change_date("ATEAM-4096")
    # print jira.get_sprint_info(1858, 60)
    # print jira.get_issue_resolved_status_by_date('ME-2628', '2016-02-02')
    print jira.html_get_total_bug_and_open_bug_trend_by_sprint(1858, 60, "ATEAM")
