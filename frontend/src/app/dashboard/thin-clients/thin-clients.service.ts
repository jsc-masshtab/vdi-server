import { Injectable } from '@angular/core';
import { IParams } from 'types';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

@Injectable({
  providedIn: 'root'
})
export class ThinClientsService {

  public params: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
    spin: true,
    nameSort: undefined
  };

  constructor(private service: Apollo) { }

  public getThinClients(queryset: any = {}): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql`
        query thin_clients(
          $ordering: String
        ){
          thin_clients_count
          thin_clients(
            ordering: $ordering
          ){
            conn_id
            user_name
            veil_connect_version
            vm_name
            tk_ip
            tk_os
            connected
            disconnected
            data_received
            last_interaction
            is_afk
          }
        }
      `,
      variables: {
        method: 'GET',
        ordering: this.params.nameSort,
        ...queryset
      }
    });
  }

  public getThinClientStatistic(queryset: any = {}): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql`
        query thin_clients(
          $limit: Int
          $offset: Int
          $ordering: String
          $conn_id: UUID
          $user_id: UUID
        ){
          thin_clients_statistics(
            limit: $limit
            offset: $offset
            ordering: $ordering
            conn_id: $conn_id
            user_id: $user_id
          ){
            id
            conn_id
            message
            created
          }
        }
    `,
      variables: {
        method: 'GET',
        ordering: this.params.nameSort,
        ...queryset
      }
    });
  }

  disconnectThinClient(conn_id: string) {
    return this.service.mutate<any>({
      mutation: gql`
        mutation thin_clients($conn_id: UUID!) {
          disconnectThinClient(conn_id: $conn_id) {
            ok
          }
        }
      `,
      variables: {
        method: 'POST',
        conn_id
      }
    });
  }

}
