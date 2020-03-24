# Retrieve payloads for DialogFlow


def get_plot_payload(imageURL):
    reply = {
        "fulfillmentText": "",
        "fulfillmentMessages": [
            {
            }
        ],
        "payload": {
            "google":
            {
                "expectUserResponse": True,
                "richResponse":
                {
                    "items": [
                        {
                            "basicCard":
                            {
                                "title": "",
                                "formattedText": "",
                                "image":
                                {
                                    "url": imageURL,
                                },
                                "buttons": [
                                    {
                                        "title": "See large image",
                                        "openUrlAction":
                                        {
                                            "url": imageURL
                                        }
                                    },
                                ]
                            },
                        }
                    ],
                }
            }
        }
    }
    return reply


def get_card_payload(textTitle, textAnswer, imageURL="",
                     sourceURL="", referenceURL="", suggestions=[]):
    reply = {
        "fulfillmentText": "",
        "fulfillmentMessages": [
            {
            }
        ],
        "source": "example.com",
        "payload": {
            "google":
            {
                "expectUserResponse": True,
                "richResponse":
                {
                    "items": [
                        {
                            "basicCard":
                            {
                                "title": textTitle,
                                "formattedText": textAnswer,
                                "image":
                                {
                                    "url": imageURL,
                                },
                                "buttons": [
                                    {
                                        "title": "Source",
                                        "openUrlAction":
                                        {
                                            "url": sourceURL
                                        }
                                    },
                                    {
                                        "title": "Learn more",
                                        "openUrlAction":
                                        {
                                            "url": referenceURL
                                        }
                                    }
                                ],
                                "imageDisplayOptions": "CROPPED"
                            },
                        }
                    ],
                    "suggestions": suggestions
                }
            }
        }
    }
    return reply
