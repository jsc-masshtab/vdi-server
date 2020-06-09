
import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class EventsService {

    constructor(private service: Apollo) { }

    public getAllEvents(props): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query events(   $limit: Int,
                                        $offset: Int,
                                        $start_date: DateTime,
                                        $end_date: DateTime,
                                        $event_type: Int,
                                        $entity_type: String,
                                        $user: String,
                                        $read_by: UUID) {
                                count(  start_date: $start_date,
                                        end_date: $end_date,
                                        event_type: $event_type,
                                        entity_type: $entity_type,
                                        user: $user,
                                        read_by: $read_by),
                                entity_types 
                                users {
                                    id
                                    username
                                }
                                events( limit: $limit,
                                        offset: $offset,
                                        start_date: $start_date,
                                        end_date: $end_date,
                                        event_type: $event_type,
                                        entity_type: $entity_type,
                                        user: $user,
                                        read_by: $read_by) {
                                    event_type
                                    description
                                    message
                                    created
                                    user
                                },
                            }
                    `,
            variables: {
                method: 'GET',
                ...props
            }
        });
    }
}

