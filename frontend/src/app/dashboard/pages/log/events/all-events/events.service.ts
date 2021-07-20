
import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { IParams } from 'types';


@Injectable()
export class EventsService {

    public paramsForGetEvents: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) { }

    public getAllEvents(props): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query events(   $limit: Int,
                                        $offset: Int,
                                        $start_date: DateTime,
                                        $end_date: DateTime,
                                        $entity: UUID,
                                        $event_type: Int,
                                        $entity_type: String,
                                        $user: String,
                                        $read_by: UUID
                                        $ordering:String) {
                                count(  start_date: $start_date,
                                        end_date: $end_date,
                                        event_type: $event_type,
                                        entity_type: $entity_type,
                                        user: $user,
                                        read_by: $read_by),
                                entity_types,
                                users{
                                  username,
                                  id
                                },
                                events( limit: $limit,
                                        offset: $offset,
                                        start_date: $start_date,
                                        end_date: $end_date,
                                        entity: $entity,
                                        event_type: $event_type,
                                        entity_type: $entity_type,
                                        user: $user,
                                        read_by: $read_by,
                                        ordering: $ordering) {
                                    entity_id
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
                ordering: this.paramsForGetEvents.nameSort,
                ...props
            }
        });
    }

    public createExport(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation events(
                    $start: DateTime,
                    $finish: DateTime,
                    $journal_path: String
                ){
                    eventExport(
                        start: $start,
                        finish: $finish,
                        journal_path: $journal_path
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }
}

