import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

@Injectable({
  providedIn: 'root'
})
export class ControllerEventsService {

  
  public paramsForGetEvents: any = { 
    spin: true,
    nameSort: undefined
  };

  constructor(private service: Apollo) { }

  public getAllEvents(props): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql`
        query events(
          $limit: Int,
          $offset: Int,
          $controller: UUID,
          $event_type: Int,
          $ordering: String
        ){
          veil_events (
            limit: $limit,
            offset: $offset,
            controller: $controller,
            event_type: $event_type,
            ordering: $ordering
          ){
            id
            message
            event_type
            user
            created
            description
          }
          veil_events_count
        }
      `,
      variables: {
        method: 'GET',
        ordering: this.paramsForGetEvents.nameSort,
        ...props
      }
    });
  }
}
