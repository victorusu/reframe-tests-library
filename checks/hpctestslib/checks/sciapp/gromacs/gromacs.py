

# import reframe as rfm

# import os
# import sys
# print(f'sys.path from {__file__}: ', sys.path, '\n')
# print(f'available modules from {__file__}:')
# for p in sys.path:
#     if not os.path.isdir(p):
#         continue
#     if p.startswith('/usr/'):
#         continue
#     if not 'checks' in p:
#         continue
#     print (f'{p}: ', os.listdir(p))
# print('\n')



# import os
# import sys
# prefix = os.path.normpath(
#     os.path.join(os.path.abspath(os.path.dirname(__file__)), *[os.pardir, os.pardir])
#     # os.path.abspath(os.path.dirname(__file__))
# )
# if not prefix in sys.path:
#     sys.path = [prefix] + sys.path

# print(f'sys.path from {__file__}: ', sys.path, '\n')
# print(f'available modules from {__file__}:')
# for p in sys.path:
#     if not os.path.isdir(p):
#         continue
#     if p.startswith('/usr/'):
#         continue

#     if not 'checks' in p:
#         continue
#     print (f'{p}: ', os.listdir(p))
# print('\n')