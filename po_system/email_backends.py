# po_system/email_backends.py - Fixed Complete Implementation

import ssl
import smtplib
import socket
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.utils import DNS_NAME
import logging

logger = logging.getLogger(__name__)

class ZeptoMailBackend(EmailBackend):
    """
    Custom email backend for Zepto Mail SMTP that handles SSL certificate verification.
    This backend resolves the SSL certificate verification issues commonly encountered
    with Zepto Mail SMTP servers.
    """
    
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, **kwargs):
        """
        Initialize the email backend with all required parameters
        """
        super().__init__(host, port, username, password, use_tls, fail_silently, 
                         use_ssl, timeout, ssl_keyfile, ssl_certfile, **kwargs)
        
        # Set default local_hostname if not provided
        if not hasattr(self, 'local_hostname') or self.local_hostname is None:
            self.local_hostname = DNS_NAME.get_fqdn()
    
    def open(self):
        """
        Ensure an open connection to the email server. Return whether or not a new
        connection was required (True or False).
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False
        
        # If local_hostname is not specified, socket.getfqdn() gets used.
        # For performance, we use the cached FQDN for local_hostname.
        connection_params = {
            'local_hostname': self.local_hostname
        } if self.local_hostname else {}
        
        try:
            # Create SSL context with relaxed certificate verification for Zepto Mail
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            logger.info(f"Connecting to {self.host}:{self.port} with user {self.username}")
            
            # Create SMTP connection
            self.connection = smtplib.SMTP(
                self.host, 
                self.port, 
                timeout=self.timeout, 
                **connection_params
            )
            
            # Enable debug output if needed (useful for troubleshooting)
            if getattr(self, 'debug', False):
                self.connection.set_debuglevel(1)
            
            # Use TLS with our custom SSL context
            if self.use_tls:
                logger.info("Starting TLS connection...")
                self.connection.starttls(context=ssl_context)
                logger.info("TLS connection established")
            
            # Authenticate if credentials are provided
            if self.username and self.password:
                logger.info(f"Authenticating with username: {self.username}")
                self.connection.login(self.username, self.password)
                logger.info("Authentication successful")
            
            return True
            
        except (smtplib.SMTPException, OSError, socket.error) as e:
            logger.error(f"Failed to connect to Zepto Mail SMTP: {e}")
            if not self.fail_silently:
                raise
            return False
    
    def close(self):
        """Close the connection to the email server."""
        if self.connection is None:
            return
        try:
            try:
                self.connection.quit()
                logger.info("SMTP connection closed gracefully")
            except (ssl.SSLError, smtplib.SMTPServerDisconnected):
                # This happens when the connection was already disconnected
                # by the server.
                self.connection.close()
                logger.info("SMTP connection force closed")
        except smtplib.SMTPException:
            if self.fail_silently:
                return
            raise
        finally:
            self.connection = None


class ZeptoMailBackendSimple(EmailBackend):
    """
    Simplified version of Zepto Mail backend - use this if the above doesn't work
    """
    
    def open(self):
        """Open connection with minimal SSL handling"""
        if self.connection:
            return False
        
        try:
            import smtplib
            import ssl
            
            # Create SSL context that ignores certificate verification
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Create SMTP connection
            self.connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            
            # Start TLS with custom context
            if self.use_tls:
                self.connection.starttls(context=context)
            
            # Login
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
            
        except Exception as e:
            if not self.fail_silently:
                raise
            return False