# 310-discussion-app
Discussion Application for CSE 310 - Python


## Rough JSON data requests and responses...will definitely need to be modified/appended to

Client sends requests to server in form; type non optional, the rest art depending on subcommand

{
  "type": "login/ag/sg/rg/logout/",
  "subcommand": "if type ag/sg/rg this field determines a subcommand 's/u/n/r/q'",
  "N": # typical quantitative modifier for all commands,
  "selections": []
  "subscriptions": [
    'group.1.com',
    'group.3.com'
    ],
  "body": {
    "group": "group name",
    "subject": "subject",
    "author": "ID or author input",
    "date": "set server side?",
    "content": "message"
    }
}

Server sends responses to client, only populated with groups client is subscribed to...

{
  "type": "error/success",
  "body": "basic information response",
  "groups": [
    {
      "name": "group name1",
      "subjects": [
        {
          "name": "subject1",
          "thread": [
            {
              "author": "id/author",
              "date": "time()",
              "content": "message"
            }
          ]
        },
        {
          "name": "subject2",
          "thread": [
            {
              "author": "id/author",
              "date": "time()",
              "content": "message"
            }
          ]
        }
      ]
    },
    {
      "name": "group name2",
      "subjects": [
        {
          "name": "subject1",
          "thread": [
            {
              "author": "id/author",
              "date": "time()",
              "content": "message"
            }
          ]
        },
        {
          "name": "subject2",
          "thread": [
            {
              "author": "id/author",
              "date": "time()",
              "content": "message"
            }
          ]
        }
      ]
    }
  ]
}
