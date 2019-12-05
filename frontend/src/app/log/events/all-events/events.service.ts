
import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class EventsService {

    constructor(private service: Apollo) {}


    public getAllEvents(): QueryRef<any, any> {

        return  this.service.watchQuery({
            query:  gql` query events {
                                events {
                                    event_type
                                    message
                                    created
                                    user
                                }
                            }
                    `,
            variables: {
                method: 'GET'
            }
        });
    }
}

