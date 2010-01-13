#!/usr/local/bin/python

# A personal Jabber bot.
# It is based on JabberBot (http://thpinfo.com/2007/python-jabberbot/).
# It replies only to the bot's owner.

username = '' # e.g. bot@jabber.org.au
password = '' # e.g. bot_password
owner = '' # e.g. bot_master@jabber.org.au

import xmpp
import inspect
import commands
import urllib

class JabberBot(object):
  command_prefix = 'bot_'

  def __init__( self, jid, password, owner, res = None):
    """Initializes the jabber bot and sets up commands."""
    self.jid = xmpp.JID( jid)
    self.password = password
    self.owner = owner
    self.res = (res or self.__class__.__name__)
    self.conn = None
    self.__finished = False

    self.commands = {}
    for (name, value) in inspect.getmembers( self):
      if inspect.ismethod( value) and name.startswith( self.command_prefix):
        self.commands[name[len(self.command_prefix):]] = value
                                
  def log( self, s):
    print '%s: %s' % ( self.__class__.__name__, s, )
        
  def connect( self): 
    if not self.conn:
      conn = xmpp.Client( self.jid.getDomain(), debug = [])
                
      if not conn.connect(): 
        self.log( 'unable to connect to server.')
        return None     
                                
      if not conn.auth( self.jid.getNode(), self.password, self.res):
        self.log( 'unable to authorize with server.')
        return None     
      
      conn.RegisterHandler( 'message', self.callback_message)
      conn.sendInitPresence()   
      self.conn = conn

    return self.conn

  def send( self, user, text, in_reply_to = None):
    """Sends a simple message to the specified user."""
    mess = xmpp.Message( user, text)
    if in_reply_to:
      mess.setThread( in_reply_to.getThread())
      mess.setType( in_reply_to.getType())

    self.connect().send( mess)

  def callback_message( self, conn, mess):
    """Messages sent to the bot will arrive here. Command handling + routing is done in this function."""
    text = mess.getBody()

    # If a message format is not supported (eg. encrypted), txt will be None
    if not text:
      return

    if ' ' in text:
      command, args = text.split(' ',1)
    else:
      command, args = text,''

    cmd = command.lower()

    if self.commands.has_key(cmd):
      reply = self.commands[cmd]( mess, args)
    else:
      reply = self.unknown_command( mess, cmd, args)
    if reply and str(mess.getFrom()).startswith(self.owner):
      self.send( mess.getFrom(), reply, mess)

  def unknown_command( self, mess, cmd, args):
    """Default handler for unknown commands

    Override this method in derived class if you 
    want to trap some unrecognized commands.  If 
    'cmd' is handled, you must return some non-false 
    value, else some helpful text will be sent back
    to the sender.
    """
    return None

  def idle_proc( self):
    """This function will be called in the main loop."""
    pass

  def serve_forever( self, connect_callback = None, disconnect_callback = None):
    """Connects to the server and handles messages."""
    conn = self.connect()
    if conn:
      self.log('bot connected. serving forever.')
    else:
      self.log('could not connect to server - aborting.')
      return

    if connect_callback:
      connect_callback()

    while not self.__finished:
      try:
        conn.Process(1)
        self.idle_proc()
      except KeyboardInterrupt:
        self.log('bot stopped by user request. shutting down.')
        break

    if disconnect_callback:
      disconnect_callback()



class PersonalJabberBot(JabberBot):

  def bot_uptime(self, mess, args):
    """Displays the output of 'uptime'"""
    return commands.getoutput('/usr/bin/uptime')

  def bot_date(self, mess, args):
    """Displays the output of 'date'"""
    return commands.getoutput('/bin/date')

  def bot_rot13(self, mess, args):
    """Returns the argument encoded in rot13"""
    return args.encode('rot13')

bot = PersonalJabberBot(username, password, owner)
bot.serve_forever()
