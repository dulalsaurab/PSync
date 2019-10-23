
## Full consumer in PSync

The current PSync library doesn't efficiently support an application to be a full consumer only - one who doesn't produce any data. This makes it harder to deploy PSync in low constraints IoT devices (consumer only) because of its intensive IBF related computation, which is mostly not needed if no data is produced. To solve the above problem, we propose to design and implement a Full Sync Consumer.

  - Designing a Full Sync Consumer à la Partial Sync consumer with the goal of simple-to-implement sync for IoT devices.
  - The device is a consumer only, it does not set a filter for sync interest. Since the device is not a producer it does not need to do calculations like IBF insertion (including hashing), IBF Compression, etc. For other devices (powerful), they can run the FullSync.
  - The device will construct an initial sync interest with a constant name for compressed empty IBF. The constructed interest will be sent to the producer. **Interest: /prefix/sync/\<IBF>**
  - Producer upon receiving the interest will reply with sync data which contains its new IBF as it does in FullSync.
  - The device will accept the data, replace its IBF with new IBF received from the gateway. **Data: /prefix/sync/\<old-IBF>/\<new-IBF>**, content ..

All other sync interest from the device will contain IBF received from the producer itself. This will significantly reduce the computation overhead of sync for low power devices whereby still performing the synchronization easily.





![aa](https://lh4.googleusercontent.com/qOgHWcNy-YyUwHPYTmtUP--rk7DHCSkh8StfEzRhBkPgZP-RqTt5FUSbgZjcZOvQuoGItRepyU3Je-wpwFc6oRYeDVwgvZO_0DudwzpBis1FDrq5DYqlBJTBbsD7BC65AqbX9q0S)

