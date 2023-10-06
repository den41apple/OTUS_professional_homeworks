content_types = {"html": "text/html",
                 "txt": "text/text",
                 "css": "text/css",
                 "js": "text/javascript",
                 "jpg": "image/jpeg",
                 "jpeg": "image/jpeg",
                 "png": "image/png",
                 "gif": "image/gif",
                 "swf": "application/x-shockwave-flash"}

response_codes = {"OK": 200,
                  "BAD_REQUEST": 400,
                  "FORBIDDEN": 403,
                  "NOT_FOUND": 404,
                  "NOT_ALLOWED": 405,
                  "INVALID_REQUEST": 422,
                  "INTERNAL_ERROR": 500, }

response_messages = {"OK": "OK",
                     "BAD_REQUEST": "Bad Request",
                     "FORBIDDEN": "Forbidden",
                     "NOT_FOUND": "Not Found",
                     "NOT_ALLOWED": "Method Not Allowed",
                     "INVALID_REQUEST": "Invalid Request",
                     "INTERNAL_ERROR": "Internal Server Error", }
