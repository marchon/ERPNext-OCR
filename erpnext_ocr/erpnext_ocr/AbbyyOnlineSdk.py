#!/usr/bin/python

# Usage: process.py <input file> <output file> [-language <Language>] [-pdf|-txt|-rtf|-docx|-xml]

import argparse
import base64
import getopt
import MultipartPostHandler
import os
import re
import sys
import time
import urllib2
import urllib
import xml.dom.minidom
import frappe


class ProcessingSettings:
    Language = "English"
    OutputFormat = "docx"


class Task:
    Status = "Unknown"
    Id = None
    DownloadUrl = None

    def IsActive(self):
        if self.Status == "InProgress" or self.Status == "Queued":
            return True
        else:
            return False


class AbbyyOnlineSdk:
    ServerUrl = "http://cloud.ocrsdk.com/"
    # ServerUrl = frappe.db.get_value("Abby OCR", None, "server_url")
    # print ServerUrl
    # To create an application and obtain a password,
    # register at http://cloud.ocrsdk.com/Account/Register
    # More info on getting your application id and password at
    # http://ocrsdk.com/documentation/faq/#faq3
    ApplicationId = "WelaSchoolSystems"
    # ApplicationId = frappe.db.get_value("Abby OCR", None, "application_id")
    # Password = "lz1N0SLtcHKq5t/oQKHpNEZY"
    Password = frappe.db.get_value("Abby OCR", None, "password")
    Proxy = None
    enableDebugging = 0

    def ProcessImage(self, filePath, settings):

        # import sys
        #
        # reload(sys)
        # sys.setdefaultencoding('utf8')

        urlParams = urllib.urlencode({
            # "language": settings.Language,
            # "exportFormat": settings.OutputFormat
        })
        # requestUrl = self.ServerUrl + "processImage?" + urlParams
        requestUrl = self.ServerUrl + "processReceipt?" + urlParams
        print requestUrl
        bodyParams = {"file": open(filePath, "rb")}
        request = urllib2.Request(requestUrl, None, self.buildAuthInfo())
        response = self.getOpener().open(request, bodyParams).read()
        if response.find('<Error>') != -1:
            return None
        # Any response other than HTTP 200 means error - in this case exception will be thrown

        # parse response xml and extract task ID
        task = self.DecodeResponse(response)
        return task

    def GetTaskStatus(self, task):
        urlParams = urllib.urlencode({"taskId": task.Id})
        statusUrl = self.ServerUrl + "getTaskStatus?" + urlParams
        request = urllib2.Request(statusUrl, None, self.buildAuthInfo())
        response = self.getOpener().open(request).read()
        task = self.DecodeResponse(response)
        return task

    def DownloadResult(self, task, outputPath):
        getResultUrl = task.DownloadUrl
        if getResultUrl == None:
            print ("No download URL found")
            return
        request = urllib2.Request(getResultUrl)
        fileResponse = self.getOpener().open(request).read()
        resultFile = open(outputPath, "wb")
        resultFile.write(fileResponse)

    def DecodeResponse(self, xmlResponse):
        """ Decode xml response of the server. Return Task object """
        dom = xml.dom.minidom.parseString(xmlResponse)
        taskNode = dom.getElementsByTagName("task")[0]
        task = Task()
        task.Id = taskNode.getAttribute("id")
        task.Status = taskNode.getAttribute("status")
        if task.Status == "Completed":
            task.DownloadUrl = taskNode.getAttribute("resultUrl")
        return task

    def buildAuthInfo(self):
        return {"Authorization": "Basic %s" % base64.b64encode("%s:%s" % (self.ApplicationId, self.Password))}

    def getOpener(self):
        if self.Proxy == None:
            self.opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler,
                                               urllib2.HTTPHandler(debuglevel=self.enableDebugging))
        else:
            self.opener = urllib2.build_opener(
                self.Proxy,
                MultipartPostHandler.MultipartPostHandler,
                urllib2.HTTPHandler(debuglevel=self.enableDebugging))
        return self.opener
