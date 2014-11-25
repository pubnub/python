from Pubnub import Pubnub
import time
import random


pubnub = Pubnub("demo","demo")
pubnub.set_u(True)

def rand_str(s):
	return str(s) + '-' + str(random.randint(1, 100000000000))


def test_1():
	channel 		= rand_str('channel')
	channel2 		= rand_str('channel')
	channel_group 	= rand_str('group')
	channel_group2  = rand_str('group')
	namespace       = rand_str('ns')

	resp = pubnub.channel_group_add_channel(channel_group=namespace + ':' + channel_group, channel=channel)
	assert resp['status'] 	== 200
	assert resp['message'] 	== 'OK'
	assert resp['error'] 	== False

	resp = pubnub.channel_group_add_channel(channel_group=namespace + ':' + channel_group, channel=channel2)
	assert resp['status'] 	== 200
	assert resp['message'] 	== 'OK'
	assert resp['error'] 	== False

	resp = pubnub.channel_group_add_channel(channel_group=namespace + ':' + channel_group2, channel=channel)
	assert resp['status'] 	== 200
	assert resp['message'] 	== 'OK'
	assert resp['error'] 	== False

	resp = pubnub.channel_group_add_channel(channel_group=namespace + ':' + channel_group2, channel=channel2)
	assert resp['status'] 	== 200
	assert resp['message'] 	== 'OK'
	assert resp['error'] 	== False


	resp = pubnub.channel_group_list_channels(channel_group=namespace + ':' + channel_group)
	assert channel in resp['payload']['channels']
	assert channel2 in resp['payload']['channels']
	assert len(resp['payload']['channels']) == 2

	resp = pubnub.channel_group_remove_channel(channel_group=namespace + ':' + channel_group, channel=channel2)
	print resp
	assert resp['status'] 	== 200
	assert resp['message'] 	== 'OK'
	assert resp['error'] 	== False

	resp = pubnub.channel_group_list_channels(channel_group=namespace + ':' + channel_group)
	print resp
	assert channel in resp['payload']['channels']
	assert len(resp['payload']['channels']) == 1


	resp = pubnub.channel_group_list_channels(channel_group=namespace + ':' + channel_group2)
	assert channel in resp['payload']['channels']
	assert channel2 in resp['payload']['channels']
	assert len(resp['payload']['channels']) == 2

	resp = pubnub.channel_group_remove_channel(channel_group=namespace + ':' + channel_group2, channel=channel2)
	print resp
	assert resp['status'] 	== 200
	assert resp['message'] 	== 'OK'
	assert resp['error'] 	== False

	resp = pubnub.channel_group_list_channels(channel_group=namespace + ':' + channel_group2)
	print resp
	assert channel in resp['payload']['channels']
	assert len(resp['payload']['channels']) == 1



	resp = pubnub.channel_group_list_groups(namespace=namespace)
	assert channel_group in resp['payload']['groups']
	assert channel_group2 in resp['payload']['groups']
	assert len(resp['payload']['groups']) == 2

	resp = pubnub.channel_group_remove_group(channel_group=namespace + ':' + channel_group2)
	print resp
	assert resp['status'] 	== 200
	assert resp['message'] 	== 'OK'
	assert resp['error'] 	== False


	resp = pubnub.channel_group_list_groups(namespace=namespace)
	assert channel_group in resp['payload']['groups']
	assert len(resp['payload']['groups']) == 1


	resp = pubnub.channel_group_list_namespaces()
	assert namespace in resp['payload']['namespaces']

	resp = pubnub.channel_group_remove_namespace(namespace=namespace)
	print resp
	assert resp['status'] 	== 200
	assert resp['message'] 	== 'OK'
	assert resp['error'] 	== False

	resp = pubnub.channel_group_list_namespaces()
	assert namespace not in resp['payload']['namespaces']




