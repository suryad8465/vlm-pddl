(define (problem manual-transfer)
  (:domain household)

  (:objects
    kitchen living_room - location
    table mug kettle - object
  )

  (:init
    (robot-at living_room)

    (connected kitchen living_room)
    (connected living_room kitchen)

    (located table kitchen)
    (located mug kitchen)
    (located kettle kitchen)

    (on mug table)
    (on kettle table)

    (manipulable mug)
    (manipulable kettle)
  )

  (:goal
    (located mug living_room)
  )
)
