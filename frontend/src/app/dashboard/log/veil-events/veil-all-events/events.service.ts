
import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { IParams } from 'types';


@Injectable()
export class VeilEventsService {

    public paramsForGetEvents: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) { }

    public getAllEvents(props): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql
            ` query
                events(
                    $limit: Int,
                    $offset: Int,
                    $controller: UUID,
                    $event_type: Int,
                    $ordering:String
                ){
                    veil_events_count,
                    veil_events(
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
                }
            `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetEvents.nameSort,
                ...props
            }
        });
    }

    public getAllControllers(): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql`
                query controllers($ordering:String) {
                    controllers(ordering: $ordering) {
                        id
                        verbose_name
                    }
                }
            `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetEvents.nameSort
            }
        });
    }
}

