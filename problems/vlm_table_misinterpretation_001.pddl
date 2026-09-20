(define (problem bring-mug-to-living-room-table)
  (:domain household)

  (:objects
    kitchen living-room - location
    table mug kettle robot - object
  )

  (:init
    (robot-at living-room)
    (connected kitchen living-room)
    (connected living-room kitchen)
    (located table kitchen)
    (located mug kitchen)
    (located kettle kitchen)
    (on mug table)
    (on kettle table)
    (manipulable mug)
    (manipulable kettle)
  )

  (:goal
    (located mug living-room)
  )
)