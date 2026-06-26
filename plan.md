# Plan Mode: WhatsApp Notification Enhancements

- [ ] Confirm that the business owner wants to receive WhatsApp messages on new booking enquiries.
- [ ] Verify that `business.whatsapp_number` is defined and formatted with country code and no leading `+` required? The current code uses `to_number` as is. Should we ensure it includes `whatsapp:` prefix? Already done.
- [ ] Consider using a more informative message body (e.g., including link to admin page for booking).
- [ ] Consider handling cases where Twilio credentials are not set: maybe display a warning in admin.
- [ ] Possibly add a test.

Current implementation sends WhatsApp immediately with static message. Next steps after user acceptance of plan.

## Regarding `deploy/home/start.sh`
The file `deploy/home/start.sh` has not been provided in the chat. Please add it so we can explain what it does.
