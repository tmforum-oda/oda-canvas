# Delete Topic use-case

This use-case describes what happens when a topic is created on the Event Management component.

* When a new topic is created the component will create two new roles: topicName.publisher & topicName.Subscriber
* An Operator could remove the privileges for components so that they no longer can publish Events
* An Operator could remove the privileges for components for them to receive Events
* The enableEventPublishing Operator should react on Topic removal (and privilege changes?)
* The enableEventSubscription Operator should react on Topic removal (and privilege changes?)

## Delete Topic

## Forbid publishing for a component

## Forbid subscribing for a component
