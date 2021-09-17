
import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '@shared/types';


@Injectable()
export class TasksService {

    public paramsForGetTasks: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) { }

    public getAllUsers(): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql` query users {
                            users {
                                username
                                id
                            }
                        }
                    `,
            variables: {
                method: 'GET'
            }
        });
    }


    public getAllTasks(props): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql`
                query tasks(
                    $limit: Int,
                    $offset: Int,
                    $task_type: PoolTaskType,
                    $status: TaskStatus,
                    $ordering:ShortString
                ){
                    tasks(
                        limit: $limit,
                        offset: $offset,
                        task_type: $task_type,
                        status: $status,
                        ordering: $ordering
                    ){
                        id
                        task_type
                        status
                        entity_id
                        priority
                        started
                        finished
                        progress
                        message
                        duration
                    },
                }
            `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetTasks.nameSort,
                ...props
            }
        });
    }

    public cancelTask(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation tasks(
                    $task: UUID
                ){
                    cancelTask(task: $task){
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

