# -*- coding: utf-8 -*-

class Dictionary:
    def __init__(self):     
        self.excite = [r'\bexcited\b',r'\bExcited\b',r'\bexcitations\b',r'\bexcitation.with',r'\bexcitation.wavelength.of',r'\bexcitation.with.a',r'\bexcitation.at',r'\bexcitations.at',r'\bexcitations.with',r'\bNUV-excitation\b',r'\bexcited.by',r'\bexcited.at',r'\bexcitation.of',r'\bexciting\b',r'\bλexc?\b',r'\bex\b',r'\bnear-UV\b',r'\\u03bbex',r'\\u03bbexc',r'\\u03bb.exc',r'\b\\u03bbexci\b',r'\bultraviolet\b',r'\bpumped\b',r'\bpumping\b',r'\bchips\b',r'\bchip\b',r'UV\b',r'\blaser\b',r'\bNUV\b',r'\bexciting.at',r'\bphotoexcitation\b',r'\bUV-excitation\b',r'\bstimulated\b',r'\bactivated\b',r'\bexcitation\b',r'\b\\u03bbext\b', r'\b\\u03bbExc\b',r'\blamp\b',r'\bUV-LEDs\b']
        self.excite_suffix = [r'λex =',r'λexc =',r'pumped by',r'excited by',r'excitation with a',r'excitation wavelength of']
        self.other = [r'\babsorption\b',r'\bLED\b',r'\birradiation\b',r'\bradiation\b',r'\bLED\b',r'\birradiated\b',r'\bLEDs\b',r'\bFWHM\b',r'\billumination\b',r'\bhalf-width\b',r'\bdiameter\b',r'\bbandwidth\b',r'\b\\u03bbLED\b', r'\bhalf.width\b',r'\bfwhm\b',r'\bhalf.maximum\b', r'\bquenched\b',r'\bquench\b']
        
#r'excitation with',r'excitations with',r'excited by',r'excitations at',r'excitation at',r'excited at',r'excitation of',r'exciting at'