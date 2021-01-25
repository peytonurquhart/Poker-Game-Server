# Poker Server
# password_verify.py
# Ensure new password follows required conventions

import sys

C_STRING = 'a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z,A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,1,2,3,4,5,6,7,8,9,0,~,!,@,#,$,%,^,&,*,(,),_,-,=,+'
ACCEPTABLE_CHARACTERS = set(C_STRING.split(','))

# Returns False if the chosen password is unacceptable, else true
    # Acceptable passwords contain:
        # Only characters in ACCEPTABLE_CHARACTERS
        # At least 8 characters
def is_acceptable_password(text):
    if set(text).issubset(ACCEPTABLE_CHARACTERS):
        pass
    else:
        return False

    if(len(text) < 8):
        return False
    
    if(len(text) > 50):
        return False

    return True

# Returns a message detailing the password requirements
def get_password_requirements_msg():
    s = "Password Requirements:\n"
    s += "Password must only contain the characters:\n"
    s += "  A-Z\n"
    s += "  a-z\n"
    s += "  0-9\n"
    s += "  ~ ! @ # $ % ^ & * ( ) _ - + =\n"
    s += "Password must be of length:\n"
    s += "  Greater than 7 characters\n"
    s += "  Less than 51 characters\n"
    return s