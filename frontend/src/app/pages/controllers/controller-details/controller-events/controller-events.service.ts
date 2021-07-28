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
        query controllers(
          $limit: Int,
          $offset: Int,
          $controller: UUID,
          $event_type: Int,
          $ordering: String
        ){
          controller(id_:$controller) {
            id
            veil_events (
              limit: $limit,
              offset: $offset,
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
            veil_events_count(event_type: $event_type)
          }
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
