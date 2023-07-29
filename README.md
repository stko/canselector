# CANSelector

The CANSelector is a software application which uses a Tweeny 4 (or other microcontrollers with two or more can busses) as a can multiplexer, where one of the different channels can be selected and all traffic is been forwarded to can 0, which is also the command can. 

The command can bit rate is fixed to actual 500k.

The other can bus speeds can be configured by the `bitrate_index`, which is hardcoded as
|value | speed   |
|------|---------|
| 0    | bus off |
| 1    | 125kb   |
| 2    | 250kb   |
| 3    | 500kb   |
| 4    | 1 Mb    |

The protocol allows 16 can busses per multiplexer and 16 multiplexers, so in total 256 addressible can busses.


## Configuration Protocol

The multiplexer(s) can be configured via CAN. The configuration is initiated by an PC application (master), which talks via CAN to the multiplexers (clients).

The design allows multiple clients and also masters on a common bus.

When having multiple masters, the last given command counts.


The configuration works as follows
At any time, the master sends a "magic telegram" on id 0x7FF (which is the only fixed telegram ID in the protokol)
* the telegram is 8 bytes long:
  * bytes 0-3 contains the String "MAFI"
  * Byte 4 & 5 contains the `sent_id` in big endian. The `sent_id` is an equal number, and the `listen_id` is `sent_id` + 1
  * Byte 6 & 7 are reserved for later extensions

When receiving this message, the clients answer with a 8 byte long `status telegram` send to `sent_id`
* bytes 0-3 contains as `client_id` a part of the internal device id as the unique identifier for that particular multiplexer.
* byte 4 contains as bitmapped data the actual active external can bus (0-15) on the MSB and the `group_id` (0-15) on the LSB.
* byte 5 LSB contains the actual `bitrate_index`
* byte 6 & 7 do contain the bus state of the first 8 can buses
  * starts with bus 0
  * 2 bits per bus
    * 00 : state unknown
    * 01 : state ok
    * 10 : disturbed: Error frames
    * 11 : Bus off

### the group id
Obviously a multiplexer could be connected randomly to any can bus group in the overall system. So how should the master know to which multiplexer a real physical bus is been connected to?

This is covered by the group id: Additionaly to the can connections each multiplexer has up to four additional pins. Whenever they are connected to ground, this is seen as a logical '1', so by that up to 16 locations can be defined which tells the multiplexer where it is connected to. This information is forwarded to master. The master application owns a system specific lookup table, which tells in which group and which channel a real bus is located. By that the master can switch to any real bus addressed by the group and channel.

### Select a channel
After the a.m. initial data exchange has been done, the master knows all available clients and to which group they are connected to. 

If now the user wants to switch to a(nother) can bus, the master sends a `config telegram` to each client:
* the can id is the `listen_id`
* the telegram is 8 bytes long:
  * bytes 0-3 contains the `client_id`
  * Byte 4 HSB contains the `channel_id` 
  * Byte 4 LSB contains the `bitrate_index`

where on all unused clients the `bitrate_index`is set to 0 to switch that client off. Only the single client which is now wanted gets the real `bitrate_index` to activate its can bus channel.

After receiving such a `config telegram` the clients switches their can busses accourdingly and reply with another `status telegram`, which is used by the masters to update their own state informations.

