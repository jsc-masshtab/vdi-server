import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { IParams } from 'types';

@Injectable()
export class VmsService {

    constructor(private service: Apollo) {}

    public params: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    public getAllVms(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query resources($ordering:String) {
                                vms(ordering: $ordering) {
                                    verbose_name
                                    status
                                    template
                                    id
                                    controller {
                                        id
                                        verbose_name
                                    }
                                }
                            }
                    `,
            variables: {
                method: 'GET',
                ordering: this.params.nameSort
            }
        });
    }

    public getVm(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query resources($id: UUID, $controller_address: UUID) {
                            vm(vm_id: $id, controller_id: $controller_address) {
                                verbose_name
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id,
                controller_address
            }
        });
    }
}
