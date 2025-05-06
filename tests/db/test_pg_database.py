from unittest.mock import patch, MagicMock
import pytest

from src.db.pg_database import PostgreSaver, IntegrityError
from src.db.pg_data_models import WeatherHourly


@pytest.fixture
def creds():
    return {
        'username': 'user',
        'password': 'pass',
        'hostname': 'localhost'
    }


@pytest.fixture
def record():
    return WeatherHourly(
        location_name='loc',
        latitude=0.0,
        longitude=1.0,
        timestamp='2025-01-01 00:00:00'
    )


@patch('src.db.pg_database.create_engine')
@patch('src.db.pg_database.sessionmaker')
def test_create_session(mock_sessionmaker, mock_create_engine, creds):
    correct_url = 'postgresql://user:pass@localhost:5432/db_name'

    pg_saver = PostgreSaver(creds)
    pg_saver._create_session('db_name')

    mock_create_engine.assert_called_once_with(correct_url)


@patch('src.db.pg_database.PostgreSaver._create_session')
def test_save_success(mock_create_session, creds, record):
    mock_session = MagicMock()
    mock_create_session.return_value = mock_session

    pg_saver = PostgreSaver(creds)
    pg_saver.save('db_name', record)

    mock_session.add.assert_called_once_with(record)
    mock_session.commit.assert_called_once()


@patch('src.db.pg_database.PostgreSaver._create_session')
@patch('src.db.pg_database.logging.getLogger')
def test_save_failure(mock_get_logger, mock_create_session, creds, record):
    mock_session = MagicMock()

    mock_diag = MagicMock()
    mock_diag.message_detail = 'Duplicate record'

    mock_orig = MagicMock()
    mock_orig.diag = mock_diag

    mock_error = IntegrityError(statement=None, params=None, orig=mock_orig)

    mock_session.commit.side_effect = mock_error
    mock_create_session.return_value = mock_session

    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    correct_error_message = 'Skippping row: Duplicate record'

    pg_saver = PostgreSaver(creds)
    pg_saver.save('db_name', record)

    mock_session.add.assert_called_once_with(record)
    mock_session.commit.assert_called_once()
    mock_logger.warning.assert_called_once_with(correct_error_message)
